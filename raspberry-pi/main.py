import time

import uvicorn
from machine.state_machine import StateMachine
from websocket.server import Server

if __name__ == "__main__":
    sm = StateMachine()
    server = Server(sm)

    uvicorn.run(app=server.app, host="0.0.0.0", port=8765, log_level="info")

    try:
        sm.start()
        while sm.update():
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("CTRL+C premuto")
    finally:
        sm.stop()
