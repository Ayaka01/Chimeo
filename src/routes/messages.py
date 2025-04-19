from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, UTC
import json
import asyncio
import logging
import uuid

from src.database import get_db
from src.models.user import DbUser
from src.models.pending_message import DbPendingMessage
from src.schemas.messages_schemas import MessageCreate, MessageResponse
from src.services.auth_service import get_current_user, decode_access_token
from src.services.message_service import (
    send_message,
    get_pending_messages,
    mark_message_delivered,
)
from src.utils.websocket_manager import connection_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/messages", tags=["messages"])

@router.post("/", response_model=MessageResponse)
async def create_message(
    message_data: MessageCreate,
    current_user: DbUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    message_id = str(uuid.uuid4())  # Use UUID to generate a unique ID

    connection = connection_manager.get_connection(message_data.recipient_username)
    
    if connection:
        try:
            logger.info(f"Attempting to send message via WebSocket to {message_data.recipient_username}")
            await connection.send_text(json.dumps({
                "type": "new_message",
                "data": {
                    "id": message_id,
                    "sender_username": current_user.username,
                    "recipient_username": message_data.recipient_username,
                    "text": message_data.text,
                    "created_at": datetime.now(UTC).isoformat(),
                    "is_delivered": True
                }
            }))
            logger.info(f"Message delivered via WebSocket to {message_data.recipient_username}")
            return MessageResponse(
                id=message_id,
                sender_username=current_user.username,
                recipient_username=message_data.recipient_username,
                text=message_data.text,
                created_at=datetime.now(UTC),
                is_delivered=True
            )
        except Exception as e:
            logger.error(f"Error delivering message via WebSocket: {e}")
    
    logger.info(f"WebSocket delivery failed or recipient offline, saving message to database for {message_data.recipient_username}")
    saved_message = send_message(
        db, 
        current_user.username, 
        message_data.recipient_username, 
        message_data.text,
        message_id=message_id
    )
    
    if not saved_message:
        logger.error(f"Failed to save message from {current_user.username} to {message_data.recipient_username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to send message. Check that you are friends with the recipient."
        )
    
    return MessageResponse(
        id=saved_message.id,
        sender_username=saved_message.sender_username,
        recipient_username=saved_message.recipient_username,
        text=saved_message.text,
        created_at=saved_message.created_at,
        is_delivered=saved_message.delivered
    )

@router.post("/delivered/{message_id}", status_code=status.HTTP_200_OK)
async def mark_message_as_delivered(
    message_id: str,
    _: DbUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = mark_message_delivered(db, message_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    message = db.query(DbPendingMessage).filter(DbPendingMessage.id == message_id).first()
    
    if message:
        sender_connection = connection_manager.get_connection(message.sender_username)
        if sender_connection:
            try:
                await sender_connection.send_text(json.dumps({
                    "type": "message_delivered",
                    "data": {"message_id": message_id}
                }))
                logger.info(f"Sent delivery notification for {message_id} to sender {message.sender_username}")
            except Exception as e:
                logger.error(f"Error notifying sender of delivery for {message_id}: {e}")
    
    return {"success": True}

@router.get("/pending", response_model=List[MessageResponse])
async def get_pending_messages_for_user(
    current_user: DbUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    messages_db = get_pending_messages(db, current_user.username, mark_delivered=False)
    return [
        MessageResponse(
            id=msg.id,
            sender_username=msg.sender_username,
            recipient_username=msg.recipient_username,
            text=msg.text,
            created_at=msg.created_at,
            is_delivered=msg.delivered
        ) for msg in messages_db
    ]

async def send_pending_messages(websocket: WebSocket, username: str, db: Session):
    pending_messages = get_pending_messages(db, username, mark_delivered=False)
    logger.info(f"Found {len(pending_messages)} pending messages for {username}")
    sent_count = 0
    for message in pending_messages:
        try:
            await websocket.send_text(json.dumps({
                "type": "new_message",
                "data": {
                    "id": message.id,
                    "sender_username": message.sender_username,
                    "recipient_username": message.recipient_username,
                    "text": message.text,
                    "created_at": message.created_at.isoformat(),
                    "is_delivered": False
                }
            }))
            logger.info(f"Sent pending message {message.id} to {username} via WebSocket")
            mark_message_delivered(db, message.id)
            sent_count += 1
            logger.info(f"Marked pending message {message.id} as delivered for {username}")
        except Exception as e:
            logger.error(f"Failed to send pending message {message.id} to {username}: {e}")
            break
    return sent_count

async def handle_client_messages(websocket: WebSocket, db: Session, username: str):
    while True:
        try:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            logger.debug(f"Received WS message from {username}: {message}")

            msg_type = message.get("type")
            if msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            elif msg_type == "message_delivered":
                message_id = message.get("data", {}).get("message_id")
                if message_id:
                    logger.info(f"Received delivery confirmation for {message_id} from {username}")
                    success = mark_message_delivered(db, message_id)
                    if success:
                         logger.info(f"Marked message {message_id} as delivered in DB")
                         delivered_message = db.query(DbPendingMessage).filter_by(id=message_id).first()
                         if delivered_message:
                             await connection_manager.send_personal_message(
                                 {"type": "message_delivered", "data": {"message_id": message_id}},
                                 delivered_message.sender_username
                             )
                             logger.info(f"Sent delivery notification for {message_id} to sender {delivered_message.sender_username}")
                    else:
                         logger.warning(f"Failed to mark message {message_id} as delivered in DB.")
            elif msg_type == "typing_indicator":
                data = message.get("data")
                if data:
                    recipient = data.get("recipient")
                    is_typing = data.get("is_typing")
                    if recipient is not None and is_typing is not None:
                        logger.info(f"Received typing indicator from {username} for {recipient}: {is_typing}")
                        await connection_manager.send_personal_message(
                            {"type": "typing_indicator", "data": {"username": username, "is_typing": is_typing}},
                            recipient
                        )
                        logger.info(f"Forwarded typing indicator from {username} to {recipient}")
            # Handle other message types if necessary

        except WebSocketDisconnect:
             logger.info(f"WebSocket disconnected for {username}")
             break
        except json.JSONDecodeError:
             logger.warning(f"Received invalid JSON from {username}")
             # Continue listening
        except Exception as e:
             logger.error(f"Error processing WebSocket message from {username}: {e}", exc_info=True)
             break # Break on unexpected errors

@router.websocket("/ws/{username}")
async def websocket_endpoint(
    websocket: WebSocket,
    username: str,
    db: Session = Depends(get_db)
):
    token = websocket.query_params.get("token")
    if not token:
        logger.warning(f"WebSocket connection attempt from {username} without token.")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        payload = decode_access_token(token)
        token_username = payload.get("sub")
        if token_username != username:
            logger.warning(f"WebSocket token mismatch for {username} (token user: {token_username})")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except Exception as e:
        logger.error(f"WebSocket authentication error for {username}: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    logger.info(f"WebSocket connection accepted for {username}")

    await connection_manager.connect(websocket, username, db)
    logger.info(f"User {username} connected and registered.")

    try:
        sent_count = await send_pending_messages(websocket, username, db)
        logger.info(f"Sent {sent_count} pending messages to {username}")
    except Exception as e:
        logger.error(f"Error sending pending messages to {username}: {e}")

    try:
        await handle_client_messages(websocket, db, username)
    except WebSocketDisconnect:
        logger.info(f"WebSocket explicitly disconnected for {username} during handling.")
    except Exception as e:
        logger.error(f"Unhandled WebSocket error for {username}: {e}", exc_info=True)
    finally:
        logger.info(f"Cleaning up WebSocket connection for {username}")
        connection_manager.disconnect(username)
