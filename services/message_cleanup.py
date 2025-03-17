from sqlalchemy.orm import Session
from models.pending_message import DbPendingMessage


def mark_message_delivered(db: Session, message_id: str):
    """Mark a message as delivered"""
    message = db.query(DbPendingMessage).filter(DbPendingMessage.id == message_id).first()
    if message:
        message.delivered = True
        db.commit()
        return True
    return False


def delete_delivered_messages(db: Session):
    """Delete all delivered messages, optionally for a specific chat room"""
    query = db.query(DbPendingMessage).filter(DbPendingMessage.delivered == True)

    messages = query.all()
    count = len(messages)

    for message in messages:
        db.delete(message)

    db.commit()
    return count
