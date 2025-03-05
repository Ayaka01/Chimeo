import json
from typing import Dict, List, Optional
from fastapi import WebSocket
from sqlalchemy.orm import Session

from services.message_cleanup import mark_message_delivered, delete_delivered_messages


class ConnectionManager:
    def __init__(self):
        # Map of user_id to websocket connection
        self.active_connections: Dict[str, WebSocket] = {}
        # Map of chat_room_id to list of user_ids
        self.chat_rooms: Dict[str, List[str]] = {}
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

        # Remove user from all chat rooms
        for room_id, users in self.chat_rooms.items():
            if user_id in users:
                users.remove(user_id)

    def join_room(self, room_id: str, user_id: str):
        if room_id not in self.chat_rooms:
            self.chat_rooms[room_id] = []

        if user_id not in self.chat_rooms[room_id]:
            self.chat_rooms[room_id].append(user_id)

    def leave_room(self, room_id: str, user_id: str):
        if room_id in self.chat_rooms and user_id in self.chat_rooms[room_id]:
            self.chat_rooms[room_id].remove(user_id)

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)

    async def broadcast_to_room(self, message: dict, room_id: str, exclude_user: str = None):
        """Send message to all users in a room and mark as delivered if sent successfully"""
        delivered_to_all = True

        if room_id in self.chat_rooms:
            for user_id in self.chat_rooms[room_id]:
                if user_id != exclude_user and user_id in self.active_connections:
                    try:
                        await self.active_connections[user_id].send_json(message)

                        # If this is a new message, mark it as delivered
                        if message.get("type") == "new_message" and "id" in message.get("data", {}):
                            message_id = message["data"]["id"]
                            if user_id in self.db_sessions:
                                mark_message_delivered(self.db_sessions[user_id], message_id)
                    except:
                        delivered_to_all = False
                else:
                    delivered_to_all = False

        return delivered_to_all

    def cleanup_delivered_messages(self, user_id: str, chat_room_id: Optional[str] = None):
        """Clean up delivered messages for a specific user"""
        if user_id in self.db_sessions:
            delete_delivered_messages(self.db_sessions[user_id], chat_room_id)


# Create a single global instance
connection_manager = ConnectionManager()
