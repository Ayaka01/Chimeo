from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class UserBase(BaseModel):
    username: str
    email: str
    display_name: str


class UserDisplay(BaseModel):
    username: str
    display_name: str
    created_at: datetime
    last_seen: datetime


class UserProfile(UserDisplay):
    is_friend: bool
    friend_request_status: Optional[str]


class FriendDisplay(BaseModel):
    username: str
    display_name: str
    last_seen: datetime
    is_online: bool


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