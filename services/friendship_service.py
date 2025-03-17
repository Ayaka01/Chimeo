# services/friendship_service.py
from typing import List
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from models.user import DbUser
from models.friendship import DbFriendRequest, DbFriendship
from services.auth_service import get_user_by_username
from services.exceptions import AlreadyFriendsError, RequestSentAlreadyError, RequestToYourselfError, UserNotFoundError


def search_users_by_query(db: Session, query: str, current_user_username: int, limit: int = 20) -> List[DbUser]:
    """Search for users by username or display name, excluding the current user"""
    return db.query(DbUser).filter(
        DbUser.username != current_user_username,
        (DbUser.username.ilike(f"%{query}%") | DbUser.display_name.ilike(f"%{query}%"))
    ).limit(limit).all()


def get_friendship(db: Session, user1_username: str, user2_username: str):
    """Check if two users are friends"""
    # Sort user IDs to ensure consistent queries regardless of who is user1/user2
    user_usernames = sorted([user1_username, user2_username])

    friendship = db.query(DbFriendship).filter(
        and_(
            DbFriendship.user1_username == user_usernames[0],
            DbFriendship.user2_username == user_usernames[1]
        )
    ).first()

    return friendship


def create_friendship(db: Session, user1_username: str, user2_username: str):
    """Create a new friendship between two users"""
    # Check if friendship already exists
    if get_friendship(db, user1_username, user2_username):
        return None

    # Sort user IDs to ensure consistent storage
    user_usernames = sorted([user1_username, user2_username])

    # Create a unique ID
    friendship_id = str(uuid.uuid4())

    # Create the friendship object
    friendship = DbFriendship(
        id=friendship_id,
        user1_username=user_usernames[0],
        user2_username=user_usernames[1],
        created_at=datetime.utcnow()
    )

    # Add and commit to database
    db.add(friendship)
    db.commit()
    db.refresh(friendship)

    return friendship


def get_friend_request(db: Session, sender_username: str, recipient_username: str):
    """Get a friend request between two users"""
    return db.query(DbFriendRequest).filter(
        and_(
            DbFriendRequest.sender_username == sender_username,
            DbFriendRequest.recipient_username == recipient_username
        )
    ).first()


def create_friend_request(db: Session, sender_username: str, recipient_username: str):
    """Create a new friend request"""
    recipient = get_user_by_username(db, recipient_username)
    if not recipient:
        raise UserNotFoundError("User not found")

    # Check if users are the same
    if sender_username == recipient_username:
        raise RequestToYourselfError("Cannot send friend request to yourself")

    # Check if request already exists
    existing_request = get_friend_request(db, sender_username, recipient_username)
    if existing_request:
        raise RequestSentAlreadyError("Friend request already sent")

    # Check if already friends
    if get_friendship(db, sender_username, recipient_username):
        raise AlreadyFriendsError("Already friends with this user")

    # Check if reverse request exists
    reverse_request = get_friend_request(db, recipient_username, sender_username)
    if reverse_request:
        reverse_request.status = "accepted"
        reverse_request.updated_at = datetime.utcnow()
        db.commit()
        return create_friendship(db, sender_username, recipient_username)

    # Create a unique ID
    request_id = str(uuid.uuid4())

    # Create the request object
    friend_request = DbFriendRequest(
        id=request_id,
        sender_username=sender_username,
        recipient_username=recipient_username,
        status="pending",
        created_at=datetime.utcnow()
    )

    # Add and commit to database
    db.add(friend_request)
    db.commit()
    db.refresh(friend_request)

    return friend_request


def accept_friend_request(db: Session, request_id: str, recipient_username: str):
    """Accept a friend request and create a friendship"""
    # Get the request
    friend_request = db.query(DbFriendRequest).filter(DbFriendRequest.id == request_id).first()

    if not friend_request:
        return None

    # Verify the recipient is the one accepting
    if friend_request.recipient_username != recipient_username:
        return None

    # Check if already accepted
    if friend_request.status == "accepted":
        return get_friendship(db, friend_request.sender_username, friend_request.recipient_username)

    # Update request status
    friend_request.status = "accepted"
    friend_request.updated_at = datetime.utcnow()

    # Create friendship
    friendship = create_friendship(db, friend_request.sender_username, friend_request.recipient_username)

    # Commit changes
    db.commit()

    return friendship


def reject_friend_request(db: Session, request_id: str, recipient_username: str):
    """Reject a friend request"""
    # Get the request
    friend_request = db.query(DbFriendRequest).filter(DbFriendRequest.id == request_id).first()

    if not friend_request:
        return None

    # Verify the recipient is the one rejecting
    if friend_request.recipient_username != recipient_username:
        return None

    # Update request status
    friend_request.status = "rejected"
    friend_request.updated_at = datetime.utcnow()

    # Commit changes
    db.commit()

    return friend_request


def get_user_friends(db: Session, username: str):
    # Query friendships where user is either user1 or user2
    friendships = db.query(DbFriendship).filter(
        or_(
            DbFriendship.user1_username == username,
            DbFriendship.user2_username == username
        )
    ).all()

    # Extract friend users
    friends = []
    for friendship in friendships:
        friend_username = friendship.user2_username if friendship.user1_username == username else friendship.user1_username
        friend = db.query(DbUser).filter(DbUser.username == friend_username).first()
        if friend:
            friends.append(friend)

    return friends


def get_user_friend_requests(db: Session, username: str, status: str = None):
    query = db.query(DbFriendRequest).filter(DbFriendRequest.recipient_username == username)

    if status:
        query = query.filter(DbFriendRequest.status == status)

    return query.all()


def get_sent_friend_requests(db: Session, username: str, status: str = None):
    query = db.query(DbFriendRequest).filter(DbFriendRequest.sender_username == username)

    if status:
        query = query.filter(DbFriendRequest.status == status)

    return query.all()


def are_friends(db: Session, user1_username: str, user2_username: str):
    return get_friendship(db, user1_username, user2_username) is not None
