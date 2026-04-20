import signal
import sys

from machine.state_machine import StateMachine
from machine.states.scan_state import ScanState

sm = StateMachine()
sm.robot.camera.start()
scan_state = ScanState(sm)
scan_state.debug = True
sm.current_state = scan_state
sm.start()


def shutdown(signum, frame):
    sm.stop()
    sys.exit(0)


signal.signal(signal.SIGINT, shutdown)   # Ctrl+C
signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGTSTP, shutdown)  # Ctrl+Z

try:
    while sm.update():
        pass
finally:
    sm.stop()
