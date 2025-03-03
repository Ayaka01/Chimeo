from sqlalchemy import Column, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base

# Association table for message participants
message_participants = Table(
    'message_participants',
    Base.metadata,
    Column('message_id', String, ForeignKey('messages.id'), primary_key=True),
    Column('user_id', String, ForeignKey('users.id'), primary_key=True)
)

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, index=True)
    sender_id = Column(String, ForeignKey("users.id"))
    chat_room_id = Column(String, ForeignKey("chat_rooms.id"))
    text = Column(String)
    timestamp = Column(DateTime, default=func.now())
    
    # Relationships
    sender = relationship("User")
    participants = relationship("User", secondary=message_participants)