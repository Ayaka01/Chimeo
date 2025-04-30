from typing import Type

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
import logging

from src.models.user import DbUser
from src.models.friendship import DbFriendRequest, DbFriendship, FriendRequestStatus
from src.services.auth_service import get_user_by_username
from src.utils.exceptions import (
    APIError, 
    UserNotFoundError, 
    FriendRequestNotFoundError, 
    FriendshipExistsError,
    FriendRequestExistsError,
    InvalidFriendRequestStateError,
    CannotFriendSelfError,
    NotAuthorizedError
)

logger = logging.getLogger(__name__)


def search_users_by_query(db: Session, query: str, current_user_username: str, limit: int = 20) -> list[Type[DbUser]]:
    # All people we already sent a friendship request to
    sent_requests_subquery = db.query(DbFriendRequest.recipient_username).filter(
        DbFriendRequest.sender_username == current_user_username
    )

    # All the people we are already friends with
    friends_subquery_1 = db.query(DbFriendship.user2_username).filter(DbFriendship.user1_username == current_user_username)
    friends_subquery_2 = db.query(DbFriendship.user1_username).filter(DbFriendship.user2_username == current_user_username)
    friends_subquery = friends_subquery_1.union(friends_subquery_2)

    return db.query(DbUser).filter(
        DbUser.username != current_user_username,
        DbUser.username.ilike(f"%{query}%"),
        DbUser.username.notin_(sent_requests_subquery),
        DbUser.username.notin_(friends_subquery)
    ).limit(limit).all()


def get_friendship(db: Session, user1_username: str, user2_username: str) -> DbFriendship | None:
    user_usernames = sorted([user1_username, user2_username])

    friendship = db.query(DbFriendship).filter(
        and_(
            DbFriendship.user1_username == user_usernames[0],
            DbFriendship.user2_username == user_usernames[1]
        )
    ).first()

    return friendship


def create_friendship(db: Session, user1_username: str, user2_username: str) -> DbFriendship:
    if get_friendship(db, user1_username, user2_username):
        raise FriendshipExistsError(f"Friendship already exists between {user1_username} and {user2_username}")

    user_usernames = sorted([user1_username, user2_username])

    friendship = DbFriendship(
        user1_username=user_usernames[0],
        user2_username=user_usernames[1],
    )

    try:
        db.add(friendship)

        request1 = get_friend_request(db, user1_username, user2_username)
        request2 = get_friend_request(db, user2_username, user1_username)
        if request1:
            db.delete(request1)
        if request2:
            db.delete(request2)

        db.commit()
        db.refresh(friendship)
        logger.info(f"Friendship created between {user_usernames[0]} and {user_usernames[1]}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating friendship between {user_usernames[0]} and {user_usernames[1]}: {e}")
        raise APIError(status_code=500, detail="Database error while creating friendship.", error_code="DB_ERROR")

    return friendship


def get_friend_request(db: Session, sender_username: str, recipient_username: str) -> DbFriendRequest | None:
    return db.query(DbFriendRequest).filter(
        and_(
            DbFriendRequest.sender_username == sender_username,
            DbFriendRequest.recipient_username == recipient_username
        )
    ).first()


def create_friend_request(db: Session, sender_username: str, recipient_username: str) -> DbFriendRequest | DbFriendship:
    if sender_username == recipient_username:
        raise CannotFriendSelfError()
        
    recipient_user = get_user_by_username(db, recipient_username)
    if not recipient_user:
        raise UserNotFoundError(f"User '{recipient_username}' not found.")
        
    if are_friends(db, sender_username, recipient_username):
        raise FriendshipExistsError(f"Already friends with {recipient_username}")

    existing_request = get_friend_request(db, sender_username, recipient_username)
    if existing_request:
        raise FriendRequestExistsError(f"Friend request to {recipient_username} already sent.")

    reverse_request = get_friend_request(db, recipient_username, sender_username)
    if reverse_request:
        logger.info(f"Found reverse request from {recipient_username}. Creating friendship with {sender_username}.")
        return create_friendship(db, sender_username, recipient_username)

    friend_request = DbFriendRequest(
        sender_username=sender_username,
        recipient_username=recipient_username
    )

    try:
        db.add(friend_request)
        db.commit()
        db.refresh(friend_request)
        logger.info(f"Friend request created from {sender_username} to {recipient_username}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating friend request from {sender_username} to {recipient_username}: {e}")
        raise APIError(status_code=500, detail="Database error while creating friend request.", error_code="DB_ERROR")

    return friend_request


def accept_friend_request(db: Session, request_id: str, current_user_username: str) -> DbFriendship:
    friend_request = db.query(DbFriendRequest).filter(DbFriendRequest.id == request_id).first()

    if not friend_request:
        raise FriendRequestNotFoundError()

    if friend_request.recipient_username != current_user_username:
        logger.warning(f"User {current_user_username} attempted to accept request {request_id} not addressed to them.")
        raise NotAuthorizedError("Cannot accept a friend request addressed to another user.")

    if friend_request.status != FriendRequestStatus.PENDING:
        logger.warning(f"Attempt to accept non-pending request {request_id} by {current_user_username}. Status: {friend_request.status}")
        raise InvalidFriendRequestStateError(f"Cannot accept friend request, status is {friend_request.status.value}.")

    friendship = create_friendship(db, str(friend_request.sender_username), str(friend_request.recipient_username))

    return friendship


def reject_friend_request(db: Session, request_id: str, current_user_username: str) -> DbFriendRequest:
    friend_request = db.query(DbFriendRequest).filter(DbFriendRequest.id == request_id).first()

    if not friend_request:
        raise FriendRequestNotFoundError()

    if friend_request.recipient_username != current_user_username:
        logger.warning(f"User {current_user_username} attempted to reject request {request_id} not addressed to them.")
        raise NotAuthorizedError("Cannot reject a friend request addressed to another user.")

    if friend_request.status != FriendRequestStatus.PENDING:
        logger.warning(f"Attempt to reject non-pending request {request_id} by {current_user_username}. Status: {friend_request.status}")
        raise InvalidFriendRequestStateError(f"Cannot reject friend request, status is {friend_request.status.value}.")
        
    friend_request.status = FriendRequestStatus.REJECTED

    try:
        db.commit()
        db.refresh(friend_request)
        logger.info(f"Friend request {request_id} rejected by {current_user_username}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error rejecting friend request {request_id}: {e}")
        raise APIError(status_code=500, detail="Database error while rejecting friend request.", error_code="DB_ERROR")
        
    return friend_request


def get_user_friends(db: Session, username: str) -> list[DbUser]:
    friendships = db.query(DbFriendship).filter(
        or_(
            DbFriendship.user1_username == username,
            DbFriendship.user2_username == username
        )
    ).all()

    friends = []
    for friendship in friendships:
        friend_username = friendship.user2_username if friendship.user1_username == username else friendship.user1_username
        friend = db.query(DbUser).filter(DbUser.username == friend_username).first()
        if friend:
            friends.append(friend)

    return friends


def get_user_friend_requests(db: Session, username: str) -> list[Type[DbFriendRequest]]:
    query = db.query(DbFriendRequest).filter(
        DbFriendRequest.recipient_username == username, 
        DbFriendRequest.status == FriendRequestStatus.PENDING)

    return query.all()


def get_sent_friend_requests(db: Session, username: str) -> list[Type[DbFriendRequest]]:
    query = db.query(DbFriendRequest).filter(
        DbFriendRequest.sender_username == username,
        DbFriendRequest.status == FriendRequestStatus.PENDING)
    
    return query.all()


def are_friends(db: Session, user1_username: str, user2_username: str):
    return get_friendship(db, user1_username, user2_username) is not None
