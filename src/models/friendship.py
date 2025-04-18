import enum
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from src.database import Base


class FriendRequestStatus(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class DbFriendRequest(Base):
    __tablename__ = "friend_requests"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    sender_username = Column(String, ForeignKey("users.username"), nullable=False)
    recipient_username = Column(String, ForeignKey("users.username"), nullable=False)
    status = Column(
        Enum(FriendRequestStatus),
        nullable=False, 
        default=FriendRequestStatus.PENDING
    )
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    sender = relationship("DbUser", foreign_keys=sender_username, back_populates="sent_friend_requests")
    recipient = relationship("DbUser", foreign_keys=recipient_username, back_populates="received_friend_requests")

    __table_args__ = (
        UniqueConstraint('sender_username', 'recipient_username', name='uq_friend_request_sender_recipient'),
    )


class DbFriendship(Base):
    __tablename__ = "friendships"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user1_username = Column(String, ForeignKey("users.username"), nullable=False)
    user2_username = Column(String, ForeignKey("users.username"), nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Ensure uniqueness of the friendship pair
    __table_args__ = (
        UniqueConstraint('user1_username', 'user2_username', name='unique_friendship'),
    )

    user1 = relationship("DbUser", foreign_keys=[user1_username])
    user2 = relationship("DbUser", foreign_keys=[user2_username])
