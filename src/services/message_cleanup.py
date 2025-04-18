from sqlalchemy.orm import Session
from src.models.pending_message import DbPendingMessage
import logging

logger = logging.getLogger(__name__)


def mark_message_delivered(db: Session, message_id: str):
    try:
        message = db.query(DbPendingMessage).filter(DbPendingMessage.id == message_id).first()
        if message:
            message.delivered = True
            db.commit()
            logger.info(f"Message {message_id} marked as delivered")
            return True
        logger.warning(f"Message {message_id} not found for delivery marking")
        return False

    except Exception as e:
        db.rollback()
        logger.error(f"Error marking message {message_id} as delivered: {e}")
        return False


def delete_delivered_messages(db: Session, user_username: str = None, cutoff_days: int = 30):
    try:
        query = db.query(DbPendingMessage).filter(DbPendingMessage.delivered == True)

        if user_username:
            query = query.filter(
                (DbPendingMessage.sender_username == user_username) | 
                (DbPendingMessage.recipient_username == user_username)
            )

        deleted_count = query.delete(synchronize_session=False)
        db.commit()
        logger.info(f"Deleted {deleted_count} delivered messages")
        return deleted_count

    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting delivered messages: {e}")
        return 0
