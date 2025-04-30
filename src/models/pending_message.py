from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from src.database import Base


class DbPendingMessage(Base):
    __tablename__ = "pending_messages"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    sender_username = Column(String, ForeignKey("users.username"), index=True, nullable=False)
    recipient_username = Column(String, ForeignKey("users.username"), index=True, nullable=False)
    text = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sender = relationship("DbUser", foreign_keys=sender_username)
    recipient = relationship("DbUser", foreign_keys=recipient_username)

    def __repr__(self):
        return f"<PendingMessage(id={self.id}, sender='{self.sender_username}', recipient='{self.recipient_username}', delivered={self.delivered})>"
