from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from database import get_db
from models.user import User
from models.chat_room import ChatRoom
from services.auth_service import get_current_user
from services.message_service import get_user_chat_rooms, get_or_create_chat_room, validate_chat_room

router = APIRouter(prefix="/chat-rooms", tags=["chat_rooms"])

# Response models


class UserInfo(BaseModel):
    id: str
    display_name: str

    class Config:
        orm_mode = True


class ChatRoomResponse(BaseModel):
    id: str
    last_message: str = None
    last_message_time: datetime = None
    participants: List[UserInfo]

    class Config:
        orm_mode = True


@router.get("/", response_model=List[ChatRoomResponse])
async def get_user_rooms(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all chat rooms for the current user (two-user chats only)"""
    chat_rooms = get_user_chat_rooms(db, current_user.id)
    return chat_rooms


@router.post("/{recipient_id}", response_model=ChatRoomResponse)
async def create_chat_room(
    recipient_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create or get a one-to-one chat room with another user"""
    if current_user.id == recipient_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create chat room with yourself"
        )

    chat_room = get_or_create_chat_room(db, current_user.id, recipient_id)

    if not chat_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found"
        )

    # Verify this is a two-user chat room
    if not validate_chat_room(db, chat_room.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only one-to-one chat rooms are allowed"
        )

    return chat_room


@router.get("/{chat_room_id}", response_model=ChatRoomResponse)
async def get_chat_room(
    chat_room_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific chat room"""
    chat_room = db.query(ChatRoom).filter(ChatRoom.id == chat_room_id).first()

    if not chat_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found"
        )

    # Check if user is a participant
    participant_ids = [user.id for user in chat_room.participants]
    if current_user.id not in participant_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this chat room"
        )

    # Verify this is a two-user chat room
    if len(chat_room.participants) != 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only one-to-one chat rooms are allowed"
        )

    return chat_room
