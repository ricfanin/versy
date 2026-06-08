# Fastapi App + Websocket

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from machine.state_machine import Job, StateMachine
from pydantic import TypeAdapter
from utils.debug import get_logger

from websocket.handlers.router import handle_message
from websocket.utils.connection_manager import ConnectionManager  # type: ignore
from websocket.utils.messages import (
    BaseMessage,
    ErrorMessage,
    IncomingMessages,
    JobInfo,
    RobotStatusMessage,
)


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

    def _job_to_info(self, job: Job) -> JobInfo:
        return JobInfo(username=job.username, marker_id=job.marker_id)

    def build_status(self) -> RobotStatusMessage:
        current = self.sm.current_job
        return RobotStatusMessage(
            state=type(self.sm.current_state).__name__,
            current_job=self._job_to_info(current) if current else None,
            queue=[self._job_to_info(j) for j in self.sm.get_queue_snapshot()],
            connected_users=self.manager.get_users(),
        )

    def publish_status(self) -> None:
        self.publish(self.build_status())

    async def websocket_endpoint(self, websocket: WebSocket):
        username = websocket.query_params.get("username", "anonymous")
        await self.manager.connect(websocket, username=username)
        self.logger.info(f"Client connesso: {websocket.client} username={username}")

        # status iniziale a questo client + broadcast lista utenti aggiornata
        await self.manager.send_message(
            self.build_status().model_dump(), websocket=websocket
        )
        self.publish_status()

        try:
            while True:
                try:
                    raw = await asyncio.wait_for(
                        websocket.receive_text(), timeout=self.INACTIVITY_TIMEOUT
                    )
                except asyncio.TimeoutError:
                    self.logger.warning(f"Timeout inattività per {websocket.client}")
                    await self.manager.disconnect(websocket, "Timeout inattività")
                    self.publish_status()
                    break

                self.logger.info(f"Messaggio ricevuto da {websocket.client}: {raw}")

                try:
                    msg = self.incoming_mex_adapter.validate_json(raw)
                    response = handle_message(msg, self.sm, username)
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
            self.publish_status()
