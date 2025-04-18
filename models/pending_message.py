"""
Pending message model for the Chimeo application.

This module defines the database model for messages that are pending delivery.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class DbPendingMessage(Base):
    """
    Pending message database model.
    
    This model stores messages that have been sent but may not yet have been
    delivered to the recipient. Messages are removed from this table once
    they've been successfully delivered and acknowledged.
    
    Attributes:
        id: Unique identifier for the message
        sender_username: Username of the user who sent the message
        recipient_username: Username of the user who should receive the message
        text: Content of the message
        created_at: Timestamp when the message was sent
        delivered: Boolean flag indicating if the message has been delivered
        
    Relationships:
        sender: Relationship to the user who sent the message
        recipient: Relationship to the user who should receive the message
    """
    __tablename__ = "pending_messages"

    id = Column(String, primary_key=True, index=True)
    sender_username = Column(String, ForeignKey("users.username"), nullable=False)
    recipient_username = Column(String, ForeignKey("users.username"), nullable=False)
    text = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    delivered = Column(Boolean, default=False)

    # Relationships
    sender = relationship("DbUser", foreign_keys=[sender_username])
    recipient = relationship("DbUser", foreign_keys=[recipient_username])
