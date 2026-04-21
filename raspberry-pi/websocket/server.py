# Fastapi App + Websocket

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import TypeAdapter 
from websocket.utils.messages import IncomingMessages, ErrorMessage
from websocket.utils.connection_manager import ConnectionManager # type: ignore
from websocket.handlers.router import handle_message
from utils.debug import get_logger
import asyncio

INACTIVITY_TIMEOUT = 300

app = FastAPI()
incoming_mex_adapter = TypeAdapter(IncomingMessages)
manager = ConnectionManager()
logger = get_logger("websocket.server")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    logger.info(f"Client connesso: {websocket.client}")

    try:
        while True:
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=INACTIVITY_TIMEOUT)
            except asyncio.TimeoutError:
                await manager.disconnect(websocket, "Timeout innattività")

            logger.info(f"Messaggio ricevuto da {websocket.client}: {raw}")

            try:
                msg = incoming_mex_adapter.validate_json(raw)
                response = handle_message(msg)
                await manager.send_message(response.model_dump(), websocket=websocket)
            except Exception as e:
                logger.error(f"Errore nel parsing/handling del messaggio: {e}")
                await websocket.send_json(
                    ErrorMessage(
                        code="INVALID_JSON",
                        message=str(e)
                    ).model_dump()
                )



    except WebSocketDisconnect:
        logger.info(f"Client disconnesso: {websocket.client}")
        await manager.disconnect(websocket, "Disconnnesione volontaria")