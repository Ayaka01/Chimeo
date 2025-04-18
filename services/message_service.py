import uuid
import logging
from datetime import datetime
from typing import List

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from models.pending_message import DbPendingMessage
from services.friendship_service import are_friends

logger = logging.getLogger(__name__)

def send_message(
    db: Session, 
    sender_username: str, 
    recipient_username: str, 
    text: str,
    message_id: str
) -> DbPendingMessage | None:
    try:
        if not are_friends(db, sender_username, recipient_username):
            logger.warning(f"Failed to send message: {sender_username} and {recipient_username} are not friends")
            return None

        message = create_pending_message(db, sender_username, recipient_username, text, message_id)
        return message
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return None

def create_pending_message(
    db: Session, 
    sender_username: str, 
    recipient_username: str, 
    text: str,
    message_id: str
) -> DbPendingMessage | None:
    try:
        message = DbPendingMessage(
            id=message_id,
            sender_username=sender_username,
            recipient_username=recipient_username,
            text=text,
            created_at=datetime.utcnow(),
            delivered=False
        )

        db.add(message)
        db.commit()
        db.refresh(message)
        
        logger.info(f"Message created from {sender_username} to {recipient_username}")
        return message
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creating message: {e}")
        return None


def get_pending_messages(
    db: Session, 
    recipient_username: str, 
    mark_delivered: bool = False
) -> List[DbPendingMessage]:
    try:
        messages = db.query(DbPendingMessage).filter(
            DbPendingMessage.recipient_username == recipient_username,
            DbPendingMessage.delivered == False
        ).all()

        if mark_delivered and messages:
            for message in messages:
                message.delivered = True
            db.commit()
            logger.info(f"Marked {len(messages)} messages as delivered for {recipient_username}")

        logger.info(f"Retrieved {len(messages)} pending messages for {recipient_username}")
        return messages
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error retrieving pending messages: {e}")
        return []


def mark_message_delivered(db: Session, message_id: str) -> bool:
    try:
        message = db.query(DbPendingMessage).filter(DbPendingMessage.id == message_id).first()

        if message:
            message.delivered = True
            db.delete(message)  # Delete the message after marking it as delivered
            db.commit()
            logger.info(f"Message {message_id} marked as delivered and deleted")
            return True

        logger.warning(f"Message {message_id} not found for delivery marking")
        return False

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error marking message as delivered: {e}")
        return False


def delete_delivered_messages(db: Session, user_username: str = None) -> int:
    try:
        query = db.query(DbPendingMessage).filter(DbPendingMessage.delivered == True)

        if user_username:
            query = query.filter(DbPendingMessage.recipient_username == user_username)

        messages = query.all()
        count = len(messages)

        for message in messages:
            db.delete(message)

        db.commit()
        
        if user_username:
            logger.info(f"Deleted {count} delivered messages for user {user_username}")
        else:
            logger.info(f"Deleted {count} delivered messages")
            
        return count
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error deleting delivered messages: {e}")
        return 0



