import asyncio
import json
import logging

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    def save_connection(self, websocket: WebSocket, username: str) -> None:
        self.active_connections[username] = websocket
        logger.info(f"User {username} WebSocket saved to Manager")

    def delete_connection(self, username: str) -> None:
        self.active_connections.pop(username, None)
        logger.info(f"User {username} WebSocket deleted from Manager")

    def get_connection(self, username: str) -> WebSocket | None:
        return self.active_connections.get(username)

    async def send_personal_message(self, message: dict, username: str):
        websocket = self.get_connection(username)
        if websocket:
            try:
                await websocket.send_text(json.dumps(message))
                logger.info(f"Sent message through WebSocket to {username}")
            except WebSocketDisconnect:
                logger.warning(f"WebSocket disconnected for {username} before message could be sent. Disconnecting.")
                self.delete_connection(username)
            except Exception as e:
                logger.error(f"Error sending personal WebSocket message to {username}: {e}")
                self.delete_connection(username)

connection_manager = ConnectionManager()
