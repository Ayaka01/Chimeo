from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class MessageCreate(BaseModel):
    recipient_username: str
    text: str


class MessageResponse(BaseModel):
    id: str
    sender_username: str
    recipient_username: str
    text: str
    created_at: datetime

    class Config:
        from_attributes = True 