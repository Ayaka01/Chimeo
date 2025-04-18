from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database import Base


class DbPendingMessage(Base):
    __tablename__ = "pending_messages"

    id = Column(String, primary_key=True, index=True)
    sender_username = Column(String, ForeignKey("users.username"), nullable=False)
    recipient_username = Column(String, ForeignKey("users.username"), nullable=False)
    text = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    delivered = Column(Boolean, default=False)

    sender = relationship("DbUser", foreign_keys=sender_username)
    recipient = relationship("DbUser", foreign_keys=recipient_username)
