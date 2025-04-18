"""
User model for the Chimeo application.

This module defines the database model for user accounts.
"""
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database import Base


class DbUser(Base):
    """
    User database model.
    
    This model stores user account information including authentication
    details and profile information.
    
    Attributes:
        username: Primary identifier for the user
        display_name: User's display name (shown in the UI)
        email: User's email address (unique)
        hashed_password: Securely hashed password
        last_seen: Timestamp of user's last activity (auto-updates)
        created_at: Timestamp of account creation
    
    Relationships:
        sent_friend_requests: Friend requests sent by this user
        received_friend_requests: Friend requests received by this user
    """
    __tablename__ = "users"

    username = Column(String, primary_key=True, index=True)
    display_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    last_seen = Column(DateTime, default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, default=func.now())

    # Relationships
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
