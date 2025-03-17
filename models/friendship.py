# models/friendship.py
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class FriendRequest(Base):
    __tablename__ = "friend_requests"

    id = Column(String, primary_key=True, index=True)
    sender_username = Column(String, ForeignKey("users.username"), nullable=False)
    recipient_username = Column(String, ForeignKey("users.username"), nullable=False)
    status = Column(String, nullable=False)  # "pending", "accepted", "rejected"
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    sender = relationship("User", foreign_keys=[sender_username], back_populates="sent_friend_requests")
    recipient = relationship("User", foreign_keys=[recipient_username], back_populates="received_friend_requests")


class Friendship(Base):
    __tablename__ = "friendships"

    id = Column(String, primary_key=True, index=True)
    user1_username = Column(String, ForeignKey("users.username"), nullable=False)
    user2_username = Column(String, ForeignKey("users.username"), nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Ensure uniqueness of the friendship pair
    __table_args__ = (
        UniqueConstraint('user1_username', 'user2_username', name='unique_friendship'),
    )

    # Relationships
    user1 = relationship("User", foreign_keys=[user1_username])
    user2 = relationship("User", foreign_keys=[user2_username])
