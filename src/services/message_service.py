import logging
from typing import List, Type

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.models.pending_message import DbPendingMessage
from src.utils.exceptions import APIError, MessageNotFoundError, UserNotFoundError
from src.services.users_service import are_friends
from src.services.auth_service import get_user_by_username

logger = logging.getLogger(__name__)

def save_message(
    db: Session, 
    sender_username: str, 
    recipient_username: str, 
    text: str,
) -> DbPendingMessage:
    recipient_user = get_user_by_username(db, recipient_username)
    if not recipient_user:
        raise UserNotFoundError(f"Recipient user '{recipient_username}' not found.")
        
    try:
        message = DbPendingMessage(
            sender_username=sender_username,
            recipient_username=recipient_username,
            text=text
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        logger.info(f"Message created from {sender_username} to {recipient_username}, ID: {message.id}")
        return message
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error saving message from {sender_username} to {recipient_username}: {e}")
        raise APIError(status_code=500, detail="Database error while saving message.", error_code="DB_ERROR")

def get_pending_messages(
    db: Session, 
    recipient_username: str
) -> List[Type[DbPendingMessage]]:
    try:
        messages = db.query(DbPendingMessage).filter(
            DbPendingMessage.recipient_username == recipient_username
        ).all()
        logger.info(f"Retrieved {len(messages)} pending messages for {recipient_username}")
        return messages
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving pending messages for {recipient_username}: {e}")
        raise APIError(status_code=500, detail="Database error while retrieving messages.", error_code="DB_ERROR")

def mark_message_delivered(db: Session, message_id: str) -> DbPendingMessage:
    try:
        message = db.query(DbPendingMessage).filter(DbPendingMessage.id == message_id).first()

        if not message:
            logger.warning(f"Message {message_id} not found for deletion.")
            raise MessageNotFoundError(f"Message with ID {message_id} not found.")

        recipient_username = message.recipient_username
        db.delete(message)
        db.commit()
        logger.info(f"Message {message_id} deleted from DB for recipient {recipient_username}.")
        return message

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"SQLAlchemyError deleting message {message_id}: {e}")
        raise APIError(status_code=500, detail="Database error while marking message delivered.", error_code="DB_ERROR")

    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error deleting message {message_id}: {e}")
        raise APIError(status_code=500, detail="Unexpected error marking message delivered.", error_code="UNEXPECTED_ERROR")



