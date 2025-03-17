from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class UserResponse(BaseModel):
    id: str
    username: str
    display_name: str
    last_seen: datetime

    class Config:
        orm_mode = True


class FriendRequestResponse(BaseModel):
    status: str

    class Config:
        orm_mode = True


class FriendRequestCreate(BaseModel):
    username: str


class FriendRequestAction(BaseModel):
    request_id: str
    action: str  # "accept" or "reject"
