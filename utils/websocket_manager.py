# utils/websocket_manager.py
from typing import Dict, List, Optional
from fastapi import WebSocket
from sqlalchemy.orm import Session

from services.message_service import mark_message_delivered


class ConnectionManager:
    def __init__(self):
        # Map of user_id to websocket connection
        self.active_connections: Dict[str, WebSocket] = {}
        # Map of user_id to database session
        self.db_sessions: Dict[str, Session] = {}

    async def connect(self, websocket: WebSocket, user_id: str, db: Session):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.db_sessions[user_id] = db

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

        if user_id in self.db_sessions:
            del self.db_sessions[user_id]

    async def send_personal_message(self, message: dict, user_id: str) -> bool:
        """Send a message to a specific user, return True if successful"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
                return True
            except Exception as e:
                print(f"Error sending message to {user_id}: {e}")
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


# Create a single global instance
connection_manager = ConnectionManager()
