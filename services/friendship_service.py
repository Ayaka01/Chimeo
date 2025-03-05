# services/friendship_service.py
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from models.user import User
from models.friendship import FriendRequest, Friendship


def get_friendship(db: Session, user1_id: str, user2_id: str):
    """Check if two users are friends"""
    # Sort user IDs to ensure consistent queries regardless of who is user1/user2
    user_ids = sorted([user1_id, user2_id])

    friendship = db.query(Friendship).filter(
        and_(
            Friendship.user1_id == user_ids[0],
            Friendship.user2_id == user_ids[1]
        )
    ).first()

    return friendship


def create_friendship(db: Session, user1_id: str, user2_id: str):
    """Create a new friendship between two users"""
    # Check if friendship already exists
    if get_friendship(db, user1_id, user2_id):
        return None

    # Sort user IDs to ensure consistent storage
    user_ids = sorted([user1_id, user2_id])

    # Create a unique ID
    friendship_id = str(uuid.uuid4())

    # Create the friendship object
    friendship = Friendship(
        id=friendship_id,
        user1_id=user_ids[0],
        user2_id=user_ids[1],
        created_at=datetime.utcnow()
    )

    # Add and commit to database
    db.add(friendship)
    db.commit()
    db.refresh(friendship)

    return friendship


def get_friend_request(db: Session, sender_id: str, recipient_id: str):
    """Get a friend request between two users"""
    return db.query(FriendRequest).filter(
        and_(
            FriendRequest.sender_id == sender_id,
            FriendRequest.recipient_id == recipient_id
        )
    ).first()


def create_friend_request(db: Session, sender_id: str, recipient_id: str):
    """Create a new friend request"""
    # Check if users are the same
    if sender_id == recipient_id:
        return None

    # Check if request already exists
    existing_request = get_friend_request(db, sender_id, recipient_id)
    if existing_request:
        return None

    # Check if reverse request exists
    reverse_request = get_friend_request(db, recipient_id, sender_id)
    if reverse_request:
        # If it's accepted, create friendship directly
        if reverse_request.status == "accepted":
            return create_friendship(db, sender_id, recipient_id)
        return None

    # Check if already friends
    if get_friendship(db, sender_id, recipient_id):
        return None

    # Create a unique ID
    request_id = str(uuid.uuid4())

    # Create the request object
    friend_request = FriendRequest(
        id=request_id,
        sender_id=sender_id,
        recipient_id=recipient_id,
        status="pending",
        created_at=datetime.utcnow()
    )

    # Add and commit to database
    db.add(friend_request)
    db.commit()
    db.refresh(friend_request)

    return friend_request


def accept_friend_request(db: Session, request_id: str, recipient_id: str):
    """Accept a friend request and create a friendship"""
    # Get the request
    friend_request = db.query(FriendRequest).filter(FriendRequest.id == request_id).first()

    if not friend_request:
        return None

    # Verify the recipient is the one accepting
    if friend_request.recipient_id != recipient_id:
        return None

    # Check if already accepted
    if friend_request.status == "accepted":
        return get_friendship(db, friend_request.sender_id, friend_request.recipient_id)

    # Update request status
    friend_request.status = "accepted"
    friend_request.updated_at = datetime.utcnow()

    # Create friendship
    friendship = create_friendship(db, friend_request.sender_id, friend_request.recipient_id)

    # Commit changes
    db.commit()

    return friendship


def reject_friend_request(db: Session, request_id: str, recipient_id: str):
    """Reject a friend request"""
    # Get the request
    friend_request = db.query(FriendRequest).filter(FriendRequest.id == request_id).first()

    if not friend_request:
        return None

    # Verify the recipient is the one rejecting
    if friend_request.recipient_id != recipient_id:
        return None

    # Update request status
    friend_request.status = "rejected"
    friend_request.updated_at = datetime.utcnow()

    # Commit changes
    db.commit()

    return friend_request


def get_user_friends(db: Session, user_id: str):
    """Get all friends of a user"""
    # Query friendships where user is either user1 or user2
    friendships = db.query(Friendship).filter(
        or_(
            Friendship.user1_id == user_id,
            Friendship.user2_id == user_id
        )
    ).all()

    # Extract friend users
    friends = []
    for friendship in friendships:
        friend_id = friendship.user2_id if friendship.user1_id == user_id else friendship.user1_id
        friend = db.query(User).filter(User.id == friend_id).first()
        if friend:
            friends.append(friend)

    return friends


def get_user_friend_requests(db: Session, user_id: str, status: str = None):
    """Get friend requests for a user with optional status filter"""
    query = db.query(FriendRequest).filter(FriendRequest.recipient_id == user_id)

    if status:
        query = query.filter(FriendRequest.status == status)

    return query.all()


def get_sent_friend_requests(db: Session, user_id: str, status: str = None):
    """Get friend requests sent by a user with optional status filter"""
    query = db.query(FriendRequest).filter(FriendRequest.sender_id == user_id)

    if status:
        query = query.filter(FriendRequest.status == status)

    return query.all()


def are_friends(db: Session, user1_id: str, user2_id: str):
    """Check if two users are friends"""
    return get_friendship(db, user1_id, user2_id) is not None
