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
    # Generate a unique message ID
    message_id = str(uuid.uuid4())  # Use UUID to generate a unique ID

    # Try to send through WebSocket if recipient is connected
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
            return {
                "id": message_id,
                "sender_username": current_user.username,
                "recipient_username": message_data.recipient_username,
                "text": message_data.text,
                "created_at": datetime.now(UTC),
                "is_delivered": True
            }
        except Exception as e:
            logger.error(f"Error delivering message via WebSocket: {e}")
    
    logger.info(f"WebSocket delivery failed, saving message to database for {message_data.recipient_username}")
    message = send_message(
        db, 
        current_user.username, 
        message_data.recipient_username, 
        message_data.text,
        message_id=message_id  # Pass the generated ID to the send_message function
    )
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to send message. Check that you are friends with the recipient."
        )
    
    return {
        "id": message.id,
        "sender_username": message.sender_username,
        "recipient_username": message.recipient_username,
        "text": message.text,
        "created_at": message.created_at,
        "is_delivered": message.delivered
    }

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
    
    # Notify sender that message was delivered
    message = db.query(DbPendingMessage).filter(DbPendingMessage.id == message_id).first()
    
    if message:
        sender_connection = connection_manager.get_connection(message.sender_username)
        if sender_connection:
            try:
                await sender_connection.send_text(json.dumps({
                    "type": "message_delivered",
                    "data": {
                        "message_id": message_id
                    }
                }))
            except Exception as e:
                logger.error(f"Error notifying sender of delivery: {e}")
    
    return {"success": True}

@router.get("/pending", response_model=List[MessageResponse])
async def get_pending_messages_for_user(
    current_user: DbUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    messages = get_pending_messages(db, current_user.username, mark_delivered=False)
    return messages

async def authenticate_websocket(websocket: WebSocket, username: str) -> bool:
    try:
        await websocket.accept()
        data = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
        message = json.loads(data)
        
        if message.get("type") != "authenticate":
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Authentication required"
            }))
            return False
            
        token = message.get("token")
        if not token:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Missing token"
            }))
            return False
            
        try:
            payload = decode_access_token(token)
            token_username = payload.get("sub")
            
            if token_username != username:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Username does not match token"
                }))
                return False
                
            return True
        except Exception as e:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Authentication failed: {str(e)}"
            }))
            return False
    except asyncio.TimeoutError:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Authentication timeout"
        }))
        return False

async def send_pending_messages(websocket: WebSocket, username: str, db: Session):
    pending_messages = get_pending_messages(db, username)
    for message in pending_messages:
        await websocket.send_text(json.dumps({
            "type": "new_message",
            "data": {
                "id": message.id,
                "sender_username": message.sender_username,
                "recipient_username": message.recipient_username,
                "text": message.text,
                "created_at": message.created_at.isoformat(),
                "delivered": False
            }
        }))
        
        mark_message_delivered(db, message.id)
    
    return len(pending_messages)

async def handle_client_messages(websocket: WebSocket, db: Session):
    while True:
        data = await websocket.receive_text()
        message = json.loads(data)
        
        if message.get("type") == "ping":
            await websocket.send_text(json.dumps({"type": "pong"}))
        elif message.get("type") == "message_delivered":
            message_id = message.get("message_id")
            if message_id:
                mark_message_delivered(db, message_id)
                
                delivered_message = db.query(DbPendingMessage).filter_by(id=message_id).first()
                if delivered_message:
                    delivery_payload = {
                        "type": "message_delivered",
                        "data": {
                            "message_id": message_id
                        }
                    }
                    
                    await connection_manager.send_personal_message(
                        delivery_payload, 
                        delivered_message.sender_username
                    )

@router.websocket("/ws/{username}")
async def websocket_endpoint(
    websocket: WebSocket,
    username: str,
    db: Session = Depends(get_db)
):
    authenticated = await authenticate_websocket(websocket, username)
    if not authenticated:
        await websocket.close()
        return
    
    await websocket.send_text(json.dumps({
        "type": "connected",
        "message": "Connected successfully"
    }))
    
    await connection_manager.connect(websocket, username, db)
    
    await send_pending_messages(websocket, username, db)
    
    try:
        await handle_client_messages(websocket, db)
    except WebSocketDisconnect:
        connection_manager.disconnect(username)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(username)
