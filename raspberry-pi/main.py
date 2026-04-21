import uvicorn
import time
from websocket.server import app
from machine.state_machine import StateMachine
from websocket.handlers.router import Router

if __name__ == "__main__":
    uvicorn.run(
        app = app,
        host="0.0.0.0",
        port=8765,
        log_level="info"
    )
    
    sm = StateMachine()
    router = Router(sm)
    try:
        sm.start()
        while sm.update():
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("CTRL+C premuto")
    finally:
        sm.stop()