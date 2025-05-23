from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from src.schemas.users_schemas import UserResponse, FriendRequestResponse, FriendRequestCreate, FriendRequestAction
from fastapi.responses import HTMLResponse
from src.database import get_db
from src.models.user import DbUser
from src.models.friendship import DbFriendRequest
from src.services.auth_service import get_current_user
from src.config import USERS_ENDPOINTS_HTML
import logging

from src.services.users_service import search_users_by_query, get_user_friends, create_friend_request, \
    accept_friend_request, reject_friend_request, get_user_friend_requests, get_sent_friend_requests
from src.utils.exceptions import APIError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_class=HTMLResponse)
async def users_root():
    return HTMLResponse(content=USERS_ENDPOINTS_HTML)


@router.get("/search", 
            response_model=List[UserResponse],
            responses={
                status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"}
            })
async def search_users(
    q: str = Query(..., min_length=3),
    db: Session = Depends(get_db),
    current_user: DbUser = Depends(get_current_user),
):
    logger.info(f"User {current_user.username} searching for users with query: {q}")
    return search_users_by_query(db, q, current_user.username)


@router.get("/friends", 
            response_model=List[UserResponse],
            responses={
                status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"}
            })
async def get_friends(
    current_user: DbUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"User {current_user.username} requested their friends list")
    return get_user_friends(db, current_user.username)


@router.post("/friends/request", 
             response_model=FriendRequestResponse,
             responses={
                 status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
                 status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation Error (e.g., invalid username format)"},
                 status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Friend request failed (e.g., DB error, already friends/requested)"}
             })
async def send_friend_request(
    request_data: FriendRequestCreate,
    current_user: DbUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"User {current_user.username} is sending friend request to {request_data.username}")
    try:
        response = create_friend_request(db, current_user.username, request_data.username)

        if isinstance(response, DbFriendRequest):
            logger.info(f"Friend request from {current_user.username} to {request_data.username} created")
            return FriendRequestResponse(
                id=response.id,
                sender_username=current_user.username,
                status="pending",
                recipient_username=request_data.username
            )
        else:
            logger.info(f"Friend request from {current_user.username} to {request_data.username} automatically accepted")
            return FriendRequestResponse(
                id=getattr(response, 'id', 'unknown'),
                sender_username=current_user.username,
                status="accepted",
                recipient_username=request_data.username
            )

    except Exception as e:
        logger.error(f"Unexpected error sending friend request from {current_user.username} to {request_data.username}: {e}", exc_info=True)
        if isinstance(e, APIError):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send friend request due to an unexpected internal error"
        )


@router.post("/friends/respond", 
             response_model=UserResponse,
             responses={
                 status.HTTP_400_BAD_REQUEST: {"description": "Invalid action ('accept' or 'reject')"},
                 status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
                 status.HTTP_404_NOT_FOUND: {"description": "Friend request not found"},
                 status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation Error"},
                 status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Could not accept/reject friend request (e.g., DB error, request invalid state)"}
             })
async def respond_to_friend_request(
    action_data: FriendRequestAction,
    current_user: DbUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"User {current_user.username} is responding to friend request {action_data.request_id} with action: {action_data.action}")
    try:
        if action_data.action == "accept":
            friendship = accept_friend_request(db, action_data.request_id, current_user.username)
            friend_username = friendship.user1_username if friendship.user2_username != current_user.username else friendship.user2_username
            friend = db.query(DbUser).filter(DbUser.username == friend_username).first()
            logger.info(f"User {current_user.username} accepted friend request from {friend_username}")
            return friend

        elif action_data.action == "reject":
            result = reject_friend_request(db, action_data.request_id, current_user.username)
            user = db.query(DbUser).filter(DbUser.username == result.sender_username).first()
            logger.info(f"User {current_user.username} rejected friend request from {result.sender_username}")
            return user

        else:
            logger.warning(f"User {current_user.username} provided invalid action for friend request: {action_data.action}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid action. Must be 'accept' or 'reject'"
            )

    except Exception as e:
        logger.error(f"Unexpected error responding to friend request {action_data.request_id} for user {current_user.username}: {e}", exc_info=True)
        if isinstance(e, APIError):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to respond to friend request due to an unexpected internal error"
        )


@router.get("/friends/requests/received", 
            response_model=List[FriendRequestResponse],
            responses={
                status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"}
            })
async def get_received_friend_requests(
    current_user: DbUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"User {current_user.username} requested received friend requests with status filter: PENDING")
    requests = get_user_friend_requests(db, current_user.username)

    return _db_friend_request_to_friend_request_response(requests)


@router.get("/friends/requests/sent", 
            response_model=List[FriendRequestResponse],
            responses={
                status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"}
            })
def get_sent_friend_requests_route(  
    current_user: DbUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"User {current_user.username} requested sent friend requests with status filter: PENDING")
    requests = get_sent_friend_requests(db, current_user.username)
    return _db_friend_request_to_friend_request_response(requests)


def _db_friend_request_to_friend_request_response(requests: List[DbFriendRequest]) -> List[FriendRequestResponse]:
    result = []
    for request in requests:
        result.append(FriendRequestResponse(
            id=request.id,
            sender_username=request.sender_username,
            recipient_username=request.recipient_username,
            status=request.status.value,
        ))
    return result
