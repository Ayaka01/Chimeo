import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.message import Message
from models.chat_room import ChatRoom, chat_room_participants
from models.user import User


def get_chat_room_id(user1_id: str, user2_id: str) -> str:
    """Generate a consistent chat room ID for two users"""
    if user1_id > user2_id:
        return f"{user1_id}-{user2_id}"
    else:
        return f"{user2_id}-{user1_id}"


def get_or_create_chat_room(db: Session, user1_id: str, user2_id: str) -> ChatRoom:
    """Get existing chat room or create a new one (strictly two users only)"""
    # Ensure we're not creating a chat with oneself
    if user1_id == user2_id:
        return None

    # Generate room ID
    room_id = get_chat_room_id(user1_id, user2_id)

    # Check if room exists
    chat_room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()

    if not chat_room:
        # Create new chat room
        chat_room = ChatRoom(id=room_id)

        # Add exactly two participants
        user1 = db.query(User).filter(User.id == user1_id).first()
        user2 = db.query(User).filter(User.id == user2_id).first()

        if user1 and user2:
            # Ensure exactly two participants
            chat_room.participants = [user1, user2]

            # Add to database
            db.add(chat_room)
            db.commit()
            db.refresh(chat_room)
        else:
            # One or both users not found
            return None

    return chat_room


def create_message(
    db: Session,
    sender_id: str,
    text: str,
    chat_room_id: str,
    participant_ids: List[str]
) -> Message:
    """Create a new message"""
    # Generate a unique ID
    message_id = str(uuid.uuid4())

    # Create message object
    db_message = Message(
        id=message_id,
        sender_id=sender_id,
        text=text,
        chat_room_id=chat_room_id,
        timestamp=datetime.utcnow(),
        delivered=False  # Initialize as not delivered
    )

    # Add participants
    for participant_id in participant_ids:
        user = db.query(User).filter(User.id == participant_id).first()
        if user:
            db_message.participants.append(user)

    # Add message to database
    db.add(db_message)

    # Update chat room's last message
    chat_room = db.query(ChatRoom).filter(ChatRoom.id == chat_room_id).first()
    if chat_room:
        chat_room.last_message = text
        chat_room.last_message_time = datetime.utcnow()

    # Commit changes
    db.commit()
    db.refresh(db_message)

    return db_message


def get_messages(db: Session, chat_room_id: str, limit: int = 50, offset: int = 0) -> List[Message]:
    """Get undelivered messages for a chat room with pagination"""
    return db.query(Message)\
             .filter(Message.chat_room_id == chat_room_id)\
             .filter(Message.delivered == False)\
             .order_by(desc(Message.timestamp))\
             .offset(offset)\
             .limit(limit)\
             .all()


def validate_chat_room(db: Session, chat_room_id: str) -> bool:
    """Validate that a chat room has exactly two participants"""
    chat_room = db.query(ChatRoom).filter(ChatRoom.id == chat_room_id).first()
    if not chat_room:
        return False

    # Check that there are exactly two participants
    return len(chat_room.participants) == 2


def get_user_chat_rooms(db: Session, user_id: str) -> List[ChatRoom]:
    """Get all chat rooms for a user (enforcing two-user limit)"""
    # Query all chat rooms where the user is a participant
    chat_rooms = db.query(ChatRoom)\
        .join(chat_room_participants)\
        .filter(chat_room_participants.c.user_id == user_id)\
        .order_by(desc(ChatRoom.last_message_time))\
        .all()

    # Filter to ensure each chat room has exactly two participants
    return [room for room in chat_rooms if len(room.participants) == 2]
