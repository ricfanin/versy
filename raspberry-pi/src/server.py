# Fastapi App + Websocket

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import TypeAdapter 
from src.utils.messages import IncomingMessages, ErrorMessage
from src.utils.connection_manager import ConnectionManager # type: ignore
from src.handlers.router import handle_message
import asyncio

INACTIVITY_TIMEOUT = 300

app = FastAPI()
incoming_mex_adapter = TypeAdapter(IncomingMessages)
manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            try: 
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=INACTIVITY_TIMEOUT)
            except asyncio.TimeoutError:
                await manager.disconnect(websocket, "Timeout innattività")

            try:
                msg = incoming_mex_adapter.validate_json(raw)
            except Exception as e:
                await websocket.send_json(
                    ErrorMessage(
                        code="INVALID_JSON",
                        message=str(e)
                    ).model_dump()
                )

            response = handle_message(msg)
            
            
    except WebSocketDisconnect: 
        await manager.disconnect(websocket, "Disconnnesione volontaria")