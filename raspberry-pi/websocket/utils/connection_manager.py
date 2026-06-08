from fastapi import WebSocket
import asyncio
from typing import Set, Dict, Optional
import logging

class ConnectionManager():
    def __init__(self):
        self.active_connections : Set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self.connection_metadata: Dict[WebSocket, dict] = {}
        self.logger = logging.getLogger(__name__)

    async def connect(self, websocket: WebSocket, username: str = "anonymous", metadata: Optional[dict] = None):
        await websocket.accept()
        self.active_connections.add(websocket)
        meta = {"username": username}
        if metadata:
            meta.update(metadata)
        self.connection_metadata[websocket] = meta


    async def disconnect(self, websocket: WebSocket, message:str = ""):
        self.active_connections.discard(websocket)
        self.connection_metadata.pop(websocket, None)
        await websocket.close(code=1000, reason=message)

    def get_users(self) -> list[str]:
        return [meta.get("username", "anonymous") for meta in self.connection_metadata.values()]

    async def send_message(self, message: dict, websocket: WebSocket):
        if websocket in self.active_connections:
            await websocket.send_json(message)


    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

    async def broadcast_except(self, message: dict, exclude: WebSocket):
        for connection in self.active_connections:
            if connection != exclude:
                await connection.send_json(message)
