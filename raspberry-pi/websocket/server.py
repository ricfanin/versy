# Fastapi App + Websocket

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from machine.state_machine import StateMachine
from pydantic import TypeAdapter
from utils.debug import get_logger

from websocket.handlers.router import handle_message
from websocket.utils.connection_manager import ConnectionManager  # type: ignore
from websocket.utils.messages import BaseMessage, ErrorMessage, IncomingMessages


class Server:
    def __init__(self, sm: StateMachine):
        self.INACTIVITY_TIMEOUT = 300
        self.sm = sm
        self.loop: asyncio.AbstractEventLoop | None = None

        @asynccontextmanager
        async def lifespan(app):
            self.loop = asyncio.get_running_loop()
            yield

        self.app = FastAPI(lifespan=lifespan)
        self.incoming_mex_adapter = TypeAdapter(IncomingMessages)
        self.manager = ConnectionManager()
        self.logger = get_logger("websocket.server")

        # Registra il route websocket
        self.app.websocket("/ws")(self.websocket_endpoint)

    def publish(self, message: BaseMessage) -> None:
        """Push thread-safe a tutti i client connessi."""
        if self.loop is None:
            self.logger.warning("publish() chiamato prima dello startup, messaggio scartato")
            return
        asyncio.run_coroutine_threadsafe(
            self.manager.broadcast(message.model_dump()),
            self.loop,
        )

    async def websocket_endpoint(self, websocket: WebSocket):
        await self.manager.connect(websocket)
        self.logger.info(f"Client connesso: {websocket.client}")

        try:
            while True:
                try:
                    raw = await asyncio.wait_for(
                        websocket.receive_text(), timeout=self.INACTIVITY_TIMEOUT
                    )
                except asyncio.TimeoutError:
                    self.logger.warning(f"Timeout inattività per {websocket.client}")
                    await self.manager.disconnect(websocket, "Timeout inattività")
                    break

                self.logger.info(f"Messaggio ricevuto da {websocket.client}: {raw}")

                try:
                    msg = self.incoming_mex_adapter.validate_json(raw)
                    response = handle_message(msg, self.sm)
                    await self.manager.send_message(
                        response.model_dump(), websocket=websocket
                    )
                except Exception as e:
                    self.logger.error(f"Errore nel parsing/handling del messaggio: {e}")
                    await websocket.send_json(
                        ErrorMessage(code="INVALID_JSON", message=str(e)).model_dump()
                    )

        except WebSocketDisconnect:
            self.logger.info(f"Client disconnesso: {websocket.client}")
            await self.manager.disconnect(websocket, "Disconnessione volontaria")
