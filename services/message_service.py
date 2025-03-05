# services/message_service.py
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from typing import List, Optional

from models.pending_message import PendingMessage
from services.friendship_service import are_friends


def create_pending_message(db: Session, sender_id: str, recipient_id: str, text: str):
    """Create a new pending message"""
    # Generate a unique ID
    message_id = str(uuid.uuid4())

    # Create the message object
    message = PendingMessage(
        id=message_id,
        sender_id=sender_id,
        recipient_id=recipient_id,
        text=text,
        created_at=datetime.utcnow(),
        delivered=False
    )

    # Add and commit to database
    db.add(message)
    db.commit()
    db.refresh(message)

    return message


def get_pending_messages(db: Session, recipient_id: str, mark_delivered: bool = False):
    """Get pending messages for a user"""
    messages = db.query(PendingMessage).filter(
        PendingMessage.recipient_id == recipient_id,
        PendingMessage.delivered == False
    ).all()

    if mark_delivered and messages:
        for message in messages:
            message.delivered = True
        db.commit()

    return messages


def mark_message_delivered(db: Session, message_id: str):
    """Mark a message as delivered"""
    message = db.query(PendingMessage).filter(PendingMessage.id == message_id).first()

    if message:
        message.delivered = True
        db.commit()
        return True

    return False


def delete_delivered_messages(db: Session, user_id: str = None):
    """Delete delivered messages, optionally for a specific user"""
    query = db.query(PendingMessage).filter(PendingMessage.delivered == True)

    if user_id:
        query = query.filter(PendingMessage.recipient_id == user_id)

    messages = query.all()

    for message in messages:
        db.delete(message)

    db.commit()
    return len(messages)


def send_message(db: Session, sender_id: str, recipient_id: str, text: str):
    """Send a message from one user to another"""
    # Verify users are friends
    if not are_friends(db, sender_id, recipient_id):
        return None

    # Create pending message
    message = create_pending_message(db, sender_id, recipient_id, text)

    return message
