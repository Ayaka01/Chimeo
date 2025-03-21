# routes/messages.py
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from database import get_db
from models.user import DbUser
from models.pending_message import DbPendingMessage
from services.auth_service import get_current_user
from services.message_service import (
    send_message,
    get_pending_messages,
    mark_message_delivered,
    delete_delivered_messages
)
from services.friendship_service import are_friends
from utils.websocket_manager import connection_manager

router = APIRouter(prefix="/messages", tags=["messages"])

# Request models


class MessageCreate(BaseModel):
    recipient_username: str
    text: str

# Response models


class MessageResponse(BaseModel):
    id: str
    sender_username: str
    recipient_username: str
    text: str
    created_at: datetime
    timestamp: datetime  # Make sure this matches the field name in PendingMessage
    delivered: bool

    class Config:
        orm_mode = True
        # If using newer versions of Pydantic (v2+), use this instead:
        # model_config = ConfigDict(from_attributes=True)

        # Add field aliases if needed
        def alias_generator(field_name): return "created_at" if field_name == "timestamp" else field_name


@router.post("/", response_model=MessageResponse)
async def send_new_message(
    message_data: MessageCreate,
    background_tasks: BackgroundTasks,
    current_user: DbUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a new message to a friend"""
    # Verify users are friends
    if not are_friends(db, current_user.username, message_data.recipient_username):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only send messages to friends"
        )

    # Create the message
    message = send_message(
        db=db,
        sender_username=current_user.username,
        recipient_username=message_data.recipient_username,
        text=message_data.text
    )

    if not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to send message"
        )

    # Try to deliver message immediately if recipient is online
    if connection_manager.is_user_online(message_data.recipient_username):
        # Prepare message data
        message_payload = {
            "type": "new_message",
            "data": {
                "id": message.id,
                "sender_username": message.sender_username,
                "text": message.text,
                "timestamp": message.created_at.isoformat(),
                "delivered": False
            }
        }

        # Send to recipient
        delivered = await connection_manager.send_personal_message(
            message=message_payload,
            username=message_data.recipient_username
        )

        # If delivered, mark as delivered and schedule cleanup
        if delivered:
            message.delivered = True
            db.commit()

            # Send delivery notification to sender
            delivery_notification = {
                "type": "message_delivered",
                "data": {
                    "message_id": message.id
                }
            }

            await connection_manager.send_personal_message(
                message=delivery_notification,
                username=current_user.username
            )

            # Schedule cleanup of delivered messages
            background_tasks.add_task(delete_delivered_messages, db)

    # Create a response that matches the expected model
    # This is needed if your SQLAlchemy model fields don't exactly match your response model
    response = {
        "id": message.id,
        "sender_username": message.sender_username,
        "recipient_username": message.recipient_username,
        "text": message.text,
        "created_at": message.created_at,  # Make sure this field exists
        "delivered": message.delivered
    }

    return response


@router.get("/pending", response_model=List[MessageResponse])
async def get_pending_messages_for_user(
    current_user: DbUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all pending messages for the current user"""
    messages = get_pending_messages(db, current_user.username, mark_delivered=False)
    return messages


@router.post("/delivered/{message_id}")
async def mark_message_as_delivered(
    message_id: str,
    background_tasks: BackgroundTasks,
    current_user: DbUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a message as delivered"""
    # Get the message
    message = db.query(PendingMessage).filter(
        PendingMessage.id == message_id,
        PendingMessage.recipient_username == current_user.username
    ).first()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    # Mark as delivered
    message.delivered = True
    db.commit()

    # Send notification to sender
    delivery_notification = {
        "type": "message_delivered",
        "data": {
            "message_id": message_id
        }
    }

    await connection_manager.send_personal_message(
        message=delivery_notification,
        username=message.sender_username
    )

    # Schedule cleanup
    background_tasks.add_task(delete_delivered_messages, db)

    return {"status": "success"}


@router.websocket("/ws/{username}")
async def websocket_endpoint(
    websocket: WebSocket,
    username: str,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time messaging"""
    # Check if user exists
    user = db.query(DbUser).filter(DbUser.username == username).first()
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Accept connection
    await connection_manager.connect(websocket, username, db)

    # Deliver any pending messages immediately
    pending_messages = get_pending_messages(db, username, mark_delivered=False)

    for message in pending_messages:
        # Format message
        message_data = {
            "type": "new_message",
            "data": {
                "id": message.id,
                "sender_username": message.sender_username,
                "text": message.text,
                "timestamp": message.created_at.isoformat(),
                "delivered": False
            }
        }

        # Send to user
        await connection_manager.send_personal_message(message_data, username)

        # Mark as delivered
        message.delivered = True

    # Commit delivery status
    if pending_messages:
        db.commit()

        # Notify senders
        for message in pending_messages:
            delivery_notification = {
                "type": "message_delivered",
                "data": {
                    "message_id": message.id
                }
            }

            await connection_manager.send_personal_message(
                message=delivery_notification,
                username=message.sender_username
            )

    try:
        # Keep connection open and listen for client messages
        while True:
            data = await websocket.receive_json()

            # Process client messages
            if data.get("type") == "message_delivered":
                message_id = data.get("message_id")
                if message_id:
                    # Mark message as delivered
                    success = await connection_manager.mark_message_delivered(message_id, username)

                    if success:
                        # Notify sender
                        message = db.query(PendingMessage).filter(PendingMessage.id == message_id).first()
                        if message:
                            delivery_notification = {
                                "type": "message_delivered",
                                "data": {
                                    "message_id": message_id
                                }
                            }

                            await connection_manager.send_personal_message(
                                message=delivery_notification,
                                username=message.sender_username
                            )

            # Heartbeat
            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        # Handle disconnect
        connection_manager.disconnect(username)
