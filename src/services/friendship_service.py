from typing import Type

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
import logging

from src.models.user import DbUser
from src.models.friendship import DbFriendRequest, DbFriendship, FriendRequestStatus

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


def create_friendship(db: Session, user1_username: str, user2_username: str) -> DbFriendship | None:
    if get_friendship(db, user1_username, user2_username):
        return None

    user_usernames = sorted([user1_username, user2_username])

    friendship = DbFriendship(
        user1_username=user_usernames[0],
        user2_username=user_usernames[1],
    )

    try:
        db.add(friendship)

        friend_request = get_friend_request(db, user1_username, user2_username)
        if friend_request:
            db.delete(friend_request)

        db.commit()
        db.refresh(friendship)
        logger.info(f"Friendship created between {user_usernames[0]} and {user_usernames[1]}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating friendship between {user_usernames[0]} and {user_usernames[1]}: {e}")
        raise

    return friendship


def get_friend_request(db: Session, sender_username: str, recipient_username: str) -> DbFriendRequest | None:
    return db.query(DbFriendRequest).filter(
        and_(
            DbFriendRequest.sender_username == sender_username,
            DbFriendRequest.recipient_username == recipient_username
        )
    ).first()


def create_friend_request(db: Session, sender_username: str, recipient_username: str) -> DbFriendRequest | None:
    reverse_request = get_friend_request(db, recipient_username, sender_username)
    if reverse_request:
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
        raise

    return friend_request


def accept_friend_request(db: Session, request_id: str, recipient_username: str) -> Type[DbFriendRequest] | None:
    friend_request = db.query(DbFriendRequest).filter(DbFriendRequest.id == request_id).first()

    if not friend_request:
        return None

    if friend_request.recipient_username != recipient_username:
        return None

    if friend_request.status != FriendRequestStatus.PENDING:
        logger.warning(f"Attempt to accept non-pending request {request_id} by {recipient_username}. Status: {friend_request.status}")
        raise ValueError(f"Friend request is not pending.")

    friendship = create_friendship(db, str(friend_request.sender_username), str(friend_request.recipient_username))

    return friendship


def reject_friend_request(db: Session, request_id: str, recipient_username: str) -> Type[DbFriendRequest] | None:
    friend_request = db.query(DbFriendRequest).filter(DbFriendRequest.id == request_id).first()

    if not friend_request:
        return None

    if friend_request.recipient_username != recipient_username:
        return None

    friend_request.status = FriendRequestStatus.REJECTED

    db.commit()

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
