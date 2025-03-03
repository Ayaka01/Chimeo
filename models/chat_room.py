from sqlalchemy import Column, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base

# Association table for chat room participants
chat_room_participants = Table(
    'chat_room_participants',
    Base.metadata,
    Column('chat_room_id', String, ForeignKey('chat_rooms.id'), primary_key=True),
    Column('user_id', String, ForeignKey('users.id'), primary_key=True)
)

class ChatRoom(Base):
    __tablename__ = "chat_rooms"
    
    id = Column(String, primary_key=True, index=True)
    last_message = Column(String, nullable=True)
    last_message_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    participants = relationship("User", secondary=chat_room_participants)
    messages = relationship("Message", backref="chat_room", cascade="all, delete-orphan")