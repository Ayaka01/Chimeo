from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class UserResponse(BaseModel):
    username: str
    display_name: str
    last_seen: datetime

    class Config:
        from_attributes = True


class FriendRequestResponse(BaseModel):
    id: str
    sender_username: str
    recipient_username: str
    status: str


class FriendRequestCreate(BaseModel):
    username: str


class FriendRequestAction(BaseModel):
    request_id: str
    action: str  