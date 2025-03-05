# routes/users.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from database import get_db
from models.user import User
from models.friendship import FriendRequest
from services.auth_service import get_current_user, get_user_by_username
from services.friendship_service import (
    create_friend_request,
    accept_friend_request,
    reject_friend_request,
    get_user_friends,
    get_user_friend_requests,
    get_sent_friend_requests,
    are_friends
)

router = APIRouter(prefix="/users", tags=["users"])

# Response models


class UserResponse(BaseModel):
    id: str
    username: str
    display_name: str
    last_seen: datetime

    class Config:
        orm_mode = True


class FriendRequestResponse(BaseModel):
    id: str
    sender: UserResponse
    recipient: UserResponse
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# Request models


class FriendRequestCreate(BaseModel):
    username: str


class FriendRequestAction(BaseModel):
    request_id: str
    action: str  # "accept" or "reject"


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@router.get("/search", response_model=List[UserResponse])
async def search_users(
    q: str = Query(..., min_length=3),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search for users by username or display name"""
    # Search for users with matching username or display name
    users = db.query(User).filter(
        User.id != current_user.id,
        (User.username.ilike(f"%{q}%") | User.display_name.ilike(f"%{q}%"))
    ).limit(20).all()

    return users


@router.get("/friends", response_model=List[UserResponse])
async def get_friends(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all friends of the current user"""
    friends = get_user_friends(db, current_user.id)
    return friends


@router.post("/friends/request", response_model=FriendRequestResponse)
async def send_friend_request(
    request_data: FriendRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a friend request to another user"""
    # Find user by username
    recipient = get_user_by_username(db, request_data.username)

    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verify not sending to self
    if recipient.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send friend request to yourself"
        )

    # Check if already friends
    if are_friends(db, current_user.id, recipient.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already friends with this user"
        )

    # Send friend request
    friend_request = create_friend_request(db, current_user.id, recipient.id)

    if not friend_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create friend request. It may already exist or there may be a pending request in the other direction."
        )

    # Fetch the request with relationships
    if isinstance(friend_request, FriendRequest):
        request = db.query(FriendRequest).filter(FriendRequest.id == friend_request.id).first()
        return request
    else:
        # If we got a friendship back, they're already friends
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already friends with this user"
        )


@router.post("/friends/respond", response_model=UserResponse)
async def respond_to_friend_request(
    action_data: FriendRequestAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accept or reject a friend request"""
    if action_data.action == "accept":
        # Accept the request
        friendship = accept_friend_request(db, action_data.request_id, current_user.id)

        if not friendship:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not accept friend request"
            )

        # Return the new friend
        friend_id = friendship.user1_id if friendship.user1_id != current_user.id else friendship.user2_id
        friend = db.query(User).filter(User.id == friend_id).first()
        return friend

    elif action_data.action == "reject":
        # Reject the request
        result = reject_friend_request(db, action_data.request_id, current_user.id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not reject friend request"
            )

        # Return the user who sent the request
        user = db.query(User).filter(User.id == result.sender_id).first()
        return user

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action. Must be 'accept' or 'reject'"
        )


@router.get("/friends/requests/received", response_model=List[FriendRequestResponse])
async def get_received_friend_requests(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get friend requests received by the current user"""
    requests = get_user_friend_requests(db, current_user.id, status)
    return requests


@router.get("/friends/requests/sent", response_model=List[FriendRequestResponse])
async def get_sent_friend_requests(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get friend requests sent by the current user"""
    requests = get_sent_friend_requests(db, current_user.id, status)
    return requests
