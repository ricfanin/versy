# Fastapi App + Websocket

from fastapi import FastAPI, WebSocket
from pydantic import TypeAdapter 
from src.utils.messages import IncomingMessages, ErrorMessage
    
app = FastAPI()
incoming_mex_adapter = TypeAdapter(IncomingMessages)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    async for raw in websocket.iter_text():
        try: 
            msg = incoming_mex_adapter.validate_json(raw)
        except Exception as e:
            await websocket.send_json(
                ErrorMessage(
                    code="INVALID_JSON",
                    message=str(e)
                ).model_dump()
            )
        
        