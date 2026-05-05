from time import sleep

from machine.state_machine import StateMachine
from machine.states.moving_state import MovingState
from machine.states.scan_state import ScanState

from websocket.utils.messages import ArucoFindMessage, ArucoFoundMessage, ErrorMessage


def aruco_handler(msg: ArucoFindMessage, sm: StateMachine):
    try:
        sm.transition_to(ScanState(sm, msg.marker_id))
        while sm.current_state != MovingState:
            sleep(0.1)  # evita busy waiting (speriamo)
        response = ArucoFoundMessage(
            marker_id=msg.marker_id,
        )
    except Exception as e:
        response = ErrorMessage(code="ARUCO_FINDING_ERROR", message=str(e))

    return response
