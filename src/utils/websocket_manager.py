import asyncio
import json
import logging
from typing import Dict, List, Optional

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_db_sessions: Dict[str, Session] = {}

    async def connect(self, websocket: WebSocket, username: str, db: Session):
        self.active_connections[username] = websocket
        self.user_db_sessions[username] = db
        logger.info(f"User {username} connected via WebSocket")

    def disconnect(self, username: str):
        if username in self.active_connections:
            del self.active_connections[username]
        if username in self.user_db_sessions:
            del self.user_db_sessions[username]
        logger.info(f"User {username} disconnected from WebSocket")

    def get_connection(self, username: str) -> Optional[WebSocket]:
        return self.active_connections.get(username)

    async def send_personal_message(self, message: dict, username: str):
        websocket = self.active_connections.get(username)
        if websocket:
            try:
                await websocket.send_text(json.dumps(message))
                logger.info(f"Sent personal WebSocket message to {username}")
            except WebSocketDisconnect:
                logger.warning(f"WebSocket disconnected for {username} before message could be sent. Disconnecting.")
                self.disconnect(username)
            except Exception as e:
                logger.error(f"Error sending personal WebSocket message to {username}: {e}")
                self.disconnect(username) # Disconnect on other errors too

    # Helper for calling async send_personal_message from sync code
    # Note: This relies on the event loop being accessible.
    # If running outside FastAPI's context, a different approach might be needed.
    def send_personal_message_sync(self, message: dict, username: str):
        websocket = self.active_connections.get(username)
        if websocket:
            try:
                loop = asyncio.get_running_loop()
                # Schedule the coroutine to run on the loop
                asyncio.run_coroutine_threadsafe(self.send_personal_message(message, username), loop)
                logger.info(f"Scheduled async personal WebSocket message to {username}")
            except RuntimeError:
                # Fallback if no running loop is found (might happen in some contexts)
                # This is less ideal as it blocks
                logger.warning(f"No running event loop found for {username}. Trying asyncio.run().")
                try:
                   asyncio.run(self.send_personal_message(message, username))
                except Exception as e:
                    logger.error(f"Error sending personal message via asyncio.run for {username}: {e}")
            except Exception as e:
                logger.error(f"Error scheduling/sending sync-to-async message for {username}: {e}")
        else:
             logger.warning(f"Attempted to send message to disconnected user: {username}")

    async def broadcast(self, message: dict):
        disconnected_users = []
        for username, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except WebSocketDisconnect:
                logger.warning(f"WebSocket disconnected for {username} during broadcast. Scheduling disconnect.")
                disconnected_users.append(username)
            except Exception as e:
                logger.error(f"Error broadcasting to {username}: {e}")
                disconnected_users.append(username)
        
        # Clean up disconnected users after broadcast attempt
        for username in disconnected_users:
            self.disconnect(username)


connection_manager = ConnectionManager()
