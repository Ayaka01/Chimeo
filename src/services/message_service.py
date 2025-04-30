import logging
from typing import List, Type

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.models.pending_message import DbPendingMessage
from src.utils.websocket_manager import connection_manager

logger = logging.getLogger(__name__)

def send_message(
    db: Session, 
    sender_username: str, 
    recipient_username: str, 
    text: str,
) -> DbPendingMessage | None:
    try:
        message: DbPendingMessage = DbPendingMessage(
            sender_username=sender_username,
            recipient_username=recipient_username,
            text=text
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
    recipient_username: str
) -> List[Type[DbPendingMessage]]:
    try:
        messages = db.query(DbPendingMessage).filter(
            DbPendingMessage.recipient_username == recipient_username
        ).all()

        logger.info(f"Retrieved {len(messages)} pending messages for {recipient_username}")
        return messages

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error retrieving pending messages: {e}")
        return []


def mark_message_delivered(db: Session, message_id: str) -> Type[DbPendingMessage] | None:
    try:
        message = db.query(DbPendingMessage).filter(DbPendingMessage.id == message_id).first()

        if message:
            recipient_username = message.recipient_username

            db.delete(message)
            db.commit()
            logger.info(f"Message {message_id} deleted from DB by {recipient_username}.")

            return message

        else:
            logger.warning(f"Message {message_id} not found for deletion.")
            return None

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"SQLAlchemyError deleting message {message_id}: {e}")
        return None

    except Exception as e:
        logger.error(f"Unexpected error deleting message {message_id}: {e}")
        return None



