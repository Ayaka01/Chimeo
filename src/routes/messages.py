from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, cast
from datetime import datetime
import json
import logging

from src.database import get_db
from src.models.user import DbUser
from src.models.pending_message import DbPendingMessage
from src.schemas.messages_schemas import MessageCreate, MessageResponse
from src.services.auth_service import get_current_user, decode_access_token
from src.services.message_service import (
    get_pending_messages,
    mark_message_delivered, save_message,
)
from src.utils.websocket_manager import connection_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/messages", tags=["messages"])

@router.post("/",
            response_model=MessageResponse,
            responses={
                status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
                status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation Error (e.g., missing fields)"},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to send message (e.g., DB error, not friends)"}
            })
async def create_message(
    message_data: MessageCreate,
    current_user: DbUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> MessageResponse:
    saved_message: DbPendingMessage = save_message(
        db,
        current_user.username,
        message_data.recipient_username,
        message_data.text,
    )

    if not saved_message:
        logger.error(f"Failed to save message from {current_user.username} to {message_data.recipient_username}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message."
        )

    connection = connection_manager.get_connection(message_data.recipient_username)

    # If recipient is online
    if connection is not None:
        logger.info(f"Recipient {message_data.recipient_username} is online. Attempting direct WS send for message {saved_message.id}.")
        try:
            # Send message to recipient via webSocket
            await connection.send_text(json.dumps({
                "type": "new_message",
                "data": {
                    "id": saved_message.id,
                    "sender_username": saved_message.sender_username,
                    "recipient_username": saved_message.recipient_username,
                    "text": saved_message.text,
                    "created_at": saved_message.created_at.isoformat(),
                }
            }))
            logger.info(f"Message {saved_message.id} sent via WebSocket to {message_data.recipient_username}")


        except Exception as e:
            logger.error(f"Error sending message {saved_message.id} via WebSocket: {e}", exc_info=True)

    logger.info(f"Responding to POST /messages/ for message {saved_message.id}")
    return MessageResponse(
        id=saved_message.id,
        sender_username=saved_message.sender_username,
        recipient_username=saved_message.recipient_username,
        text=saved_message.text,
        created_at=saved_message.created_at,
    )

@router.post("/delivered/{message_id}",
             status_code=status.HTTP_204_NO_CONTENT,
             responses={
                 status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
                 status.HTTP_403_FORBIDDEN: {"description": "Cannot mark message for another user"},
                 status.HTTP_404_NOT_FOUND: {"description": "Message not found"}
             })
async def mark_message_as_delivered(
    message_id: str,
    background_tasks: BackgroundTasks,
    current_user: DbUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> None:
    message = mark_message_delivered(db, message_id)

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found or cannot be marked as delivered."
        )

    if message.recipient_username != current_user.username:
        logger.warning(f"User {current_user.username} attempted to mark message {message_id} for recipient {message.recipient_username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot mark message as delivered for another user."
        )

    background_tasks.add_task(
        connection_manager.send_personal_message,
        {"type": "message_delivered", "data": {"message_id": message_id}},
        message.sender_username
    )

@router.get("/pending", 
            response_model=List[MessageResponse],
            responses={
                status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"}
            })
async def get_pending_messages_for_user(
    current_user: DbUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> list[MessageResponse]:
    messages_db = get_pending_messages(db, current_user.username)
    return [
        MessageResponse(
            id=str(msg.id),
            sender_username=str(msg.sender_username),
            recipient_username=str(msg.recipient_username),
            text=str(msg.text),
            created_at=cast(datetime, msg.created_at)
        ) for msg in messages_db
    ]

@router.websocket("/ws/{username}")
async def websocket_endpoint(
    websocket: WebSocket,
    username: str,
    db: Session = Depends(get_db)
) -> None:

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

    connection_manager.save_connection(websocket, username)
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
        connection_manager.delete_connection(username)


async def send_pending_messages(websocket: WebSocket, username: str, db: Session):
    pending_messages = get_pending_messages(db, username)
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
                }
            }))

            logger.info(f"Sent pending message {message.id} to {username} via WebSocket")
            mark_message_delivered(db, str(message.id))
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

            match msg_type:
                case "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))

                case "message_delivered":
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

        except WebSocketDisconnect:
             logger.info(f"WebSocket disconnected for {username}")
             break
        except json.JSONDecodeError:
             logger.warning(f"Received invalid JSON from {username}")
             # Continue listening
        except Exception as e:
             logger.error(f"Error processing WebSocket message from {username}: {e}", exc_info=True)
             break # Break on unexpected errors

