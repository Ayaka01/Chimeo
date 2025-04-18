# utils/websocket_manager.py
from typing import Dict, List, Optional
from fastapi import WebSocket
from sqlalchemy.orm import Session
import json
import logging

from services.message_service import mark_message_delivered

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        # Map of user_id to websocket connection
        self.active_connections: Dict[str, WebSocket] = {}
        # Map of user_id to database session
        self.db_sessions: Dict[str, Session] = {}

    async def connect(self, websocket: WebSocket, user_id: str, db: Session):
        self.active_connections[user_id] = websocket
        self.db_sessions[user_id] = db
        logger.info(f"User {user_id} connected")
        # Notify client about the online status
        await websocket.send_text(json.dumps({"type": "status_update", "status": "online"}))

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected")
            # Notify client about the offline status
            # Note: This needs to be handled differently as the connection is closed
            # Consider broadcasting to other users or using a different mechanism to update status

        if user_id in self.db_sessions:
            del self.db_sessions[user_id]

    async def send_personal_message(self, message: dict, user_id: str) -> bool:
        """Send a message to a specific user, return True if successful"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(json.dumps(message))
                return True
            except Exception as e:
                logger.error(f"Error sending message to {user_id}: {e}")
                return False
        return False

    async def broadcast_to_users(self, message: dict, user_ids: List[str]) -> List[str]:
        """
        Send message to multiple users
        Returns a list of user_ids that successfully received the message
        """
        successful_deliveries = []

        for user_id in user_ids:
            if await self.send_personal_message(message, user_id):
                successful_deliveries.append(user_id)

        return successful_deliveries

    async def mark_message_delivered(self, message_id: str, user_id: str) -> bool:
        """Mark a message as delivered in the database"""
        if user_id in self.db_sessions:
            return mark_message_delivered(self.db_sessions[user_id], message_id)
        return False

    def is_user_online(self, user_id: str) -> bool:
        """Check if a user is online"""
        return user_id in self.active_connections

    def get_connection(self, user_id: str) -> Optional[WebSocket]:
        """Retrieve the WebSocket connection for a specific user"""
        return self.active_connections.get(user_id)


# Create a single global instance
connection_manager = ConnectionManager()
