# routes/users.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from schemas.users_schemas import UserResponse, FriendRequestResponse, FriendRequestCreate, FriendRequestAction

from database import get_db
from models.user import DbUser
from models.friendship import DbFriendRequest, DbFriendship
from services.auth_service import get_current_user, get_user_by_username
from services.exceptions import BadRequestError, RequestToYourselfError, UserNotFoundError
from services.friendship_service import (
    create_friend_request,
    accept_friend_request,
    reject_friend_request,
    get_user_friends,
    get_user_friend_requests,
    get_sent_friend_requests,
    are_friends,
    search_users_by_query
)
from fastapi.logger import logger
router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: DbUser = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@router.get("/search", response_model=List[UserResponse])
async def search_users(
    q: str = Query(..., min_length=3),
    current_user: DbUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search for users by username or display name"""
    return search_users_by_query(db, q, current_user.username)  #


@router.get("/friends", response_model=List[UserResponse])
async def get_friends(
    current_user: DbUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all friends of the current user"""
    return get_user_friends(db, current_user.username)


@router.post("/friends/request", response_model=FriendRequestResponse)
async def send_friend_request(
    request_data: FriendRequestCreate,
    current_user: DbUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a friend request to another user"""
    try:
        response = create_friend_request(db, current_user.username, request_data.username)
    except BadRequestError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    if isinstance(response, FriendRequest):
        return FriendRequestResponse(status="pending")
    # If the request had a reversed request
    elif isinstance(response, Friendship):
        return FriendRequestResponse(status="accepted")


@router.post("/friends/respond", response_model=UserResponse)
async def respond_to_friend_request(
    action_data: FriendRequestAction,
    current_user: DbUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accept or reject a friend request"""
    if action_data.action == "accept":
        # Accept the request
        friendship = accept_friend_request(db, action_data.request_id, current_user.username)

        if not friendship:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not accept friend request"
            )

        # Return the new friend
        friend_username = friendship.user1_username if friendship.user1_username != current_user.username else friendship.user2_username
        friend = db.query(User).filter(User.username == friend_username).first()
        return friend

    elif action_data.action == "reject":
        # Reject the request
        result = reject_friend_request(db, action_data.request_id, current_user.username)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not reject friend request"
            )

        # Return the user who sent the request
        user = db.query(User).filter(User.username == result.sender_username).first()
        return user

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action. Must be 'accept' or 'reject'"
        )


@router.get("/friends/requests/received", response_model=List[FriendRequestResponse])
async def get_received_friend_requests(
    status: Optional[str] = None,
    current_user: DbUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    requests = get_user_friend_requests(db, current_user.username, status)

    return _DbFriendRequestToFriendRequestResponse(requests, db)



@router.get("/friends/requests/sent", response_model=List[FriendRequestResponse])
def get_sent_friend_requests_route(  # Renamed function to avoid name conflict
    status: Optional[str] = None,
    current_user: DbUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Direct call to the service function (which is not async)
    requests = get_sent_friend_requests(db, current_user.username, status)
    return _DbFriendRequestToFriendRequestResponse(requests, db)


def _DbFriendRequestToFriendRequestResponse(requests, db: Session):
    result = []
    for request in requests:
        sender_rq = get_user_by_username(db, request.sender_username)
        recipient_rq = get_user_by_username(db, request.recipient_username)
        sender_ur = UserResponse(username = sender_rq.username, display_name = sender_rq.display_name, last_seen = sender_rq.last_seen)
        recipient_ur = UserResponse(username = recipient_rq.username, display_name = recipient_rq.display_name, last_seen = recipient_rq.last_seen)
        result.append(FriendRequestResponse(
            id = request.id,
            sender = sender_ur,
            recipient = recipient_ur,
            status = request.status,
            created_at = request.created_at,
            updated_at = request.updated_at,
        ))
    return result
