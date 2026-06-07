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

    async def connect(self, websocket: WebSocket, metadata: Optional[dict] = None):
        await websocket.accept()
        self.active_connections.add(websocket)
        

    async def disconnect(self, websocket: WebSocket, message:str = ""):
        self.active_connections.discard(websocket)
        await websocket.close(code=1000, reason=message)

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