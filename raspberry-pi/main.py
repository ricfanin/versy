import threading
import time

import uvicorn
from machine.state_machine import StateMachine
from websocket.server import Server


def _run_uvicorn(app):
    config = uvicorn.Config(app=app, host="0.0.0.0", port=8765, log_level="info")
    server = uvicorn.Server(config)
    server.install_signal_handlers = lambda: None
    server.run()


if __name__ == "__main__":
    sm = StateMachine()
    server = Server(sm)

    uvicorn_thread = threading.Thread(
        target=_run_uvicorn, args=(server.app,), daemon=True
    )
    uvicorn_thread.start()

    try:
        sm.start()
        while sm.update():
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("CTRL+C premuto")
    finally:
        sm.stop()
