from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from database import get_db
from models.user import User
from models.message import Message
from services.auth_service import get_current_user
from services.message_service import get_messages, create_message, get_or_create_chat_room
from utils.websocket_manager import connection_manager

router = APIRouter(prefix="/messages", tags=["messages"])

# Request models
class MessageCreate(BaseModel):
    text: str
    chat_room_id: Optional[str] = None
    recipient_id: Optional[str] = None

# Response models
class MessageResponse(BaseModel):
    id: str
    sender_id: str
    text: str
    timestamp: datetime
    chat_room_id: str
    
    class Config:
        orm_mode = True

@router.post("/", response_model=MessageResponse)
async def send_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a new message"""
    chat_room_id = message_data.chat_room_id
    
    # If no chat room ID provided, create room with recipient
    if not chat_room_id and message_data.recipient_id:
        chat_room = get_or_create_chat_room(
            db, 
            current_user.id, 
            message_data.recipient_id
        )
        
        if not chat_room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipient not found"
            )
            
        chat_room_id = chat_room.id
    elif not chat_room_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either chat_room_id or recipient_id must be provided"
        )
        
    # Get participants for the message
    chat_room = get_or_create_chat_room(db, current_user.id, message_data.recipient_id)
    participant_ids = [user.id for user in chat_room.participants]
    
    # Create message in database
    message = create_message(
        db=db,
        sender_id=current_user.id,
        text=message_data.text,
        chat_room_id=chat_room_id,
        participant_ids=participant_ids
    )
    
    # Broadcast to WebSocket connections if any
    message_data = {
        "type": "new_message",
        "data": {
            "id": message.id,
            "sender_id": message.sender_id,
            "text": message.text,
            "chat_room_id": message.chat_room_id,
            "timestamp": message.timestamp.isoformat()
        }
    }
    
    await connection_manager.broadcast_to_room(
        message=message_data,
        room_id=chat_room_id,
        exclude_user=current_user.id
    )
    
    return message

@router.get("/{chat_room_id}", response_model=List[MessageResponse])
async def get_chat_messages(
    chat_room_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get messages for a chat room"""
    messages = get_messages(db, chat_room_id, limit, offset)
    return messages

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time messaging"""
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
    # Accept connection
    await connection_manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive JSON data
            data = await websocket.receive_json()
            
            # Process message data
            if data.get("type") == "join_room":
                room_id = data.get("room_id")
                if room_id:
                    connection_manager.join_room(room_id, user_id)
                    
            elif data.get("type") == "leave_room":
                room_id = data.get("room_id")
                if room_id:
                    connection_manager.leave_room(room_id, user_id)
                    
    except WebSocketDisconnect:
        # Remove from connections on disconnect
        connection_manager.disconnect(user_id)