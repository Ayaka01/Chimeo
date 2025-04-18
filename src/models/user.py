from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database import Base


class DbUser(Base):
    __tablename__ = "users"

    username = Column(String, primary_key=True, index=True)
    display_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    last_seen = Column(DateTime, default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, default=func.now())

    sent_friend_requests = relationship(
        "DbFriendRequest",
        foreign_keys="DbFriendRequest.sender_username",
        back_populates="sender",
        cascade="all, delete-orphan"
    )
    received_friend_requests = relationship(
        "DbFriendRequest",
        foreign_keys="DbFriendRequest.recipient_username",
        back_populates="recipient",
        cascade="all, delete-orphan"
    )
