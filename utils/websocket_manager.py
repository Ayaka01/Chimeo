import json
from typing import Dict, List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # Map of user_id to websocket connection
        self.active_connections: Dict[str, WebSocket] = {}
        # Map of chat_room_id to list of user_ids
        self.chat_rooms: Dict[str, List[str]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            
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
        if room_id in self.chat_rooms:
            for user_id in self.chat_rooms[room_id]:
                if user_id != exclude_user and user_id in self.active_connections:
                    await self.active_connections[user_id].send_json(message)

# Create a single global instance
connection_manager = ConnectionManager()