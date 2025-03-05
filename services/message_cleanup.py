from sqlalchemy.orm import Session
from models.message import Message


def mark_message_delivered(db: Session, message_id: str):
    """Mark a message as delivered"""
    message = db.query(Message).filter(Message.id == message_id).first()
    if message:
        message.delivered = True
        db.commit()
        return True
    return False


def delete_delivered_messages(db: Session, chat_room_id: str = None):
    """Delete all delivered messages, optionally for a specific chat room"""
    query = db.query(Message).filter(Message.delivered == True)

    if chat_room_id:
        query = query.filter(Message.chat_room_id == chat_room_id)

    messages = query.all()
    count = len(messages)

    for message in messages:
        db.delete(message)

    db.commit()
    return count
