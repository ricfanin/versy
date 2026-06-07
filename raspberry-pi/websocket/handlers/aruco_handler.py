from machine.state_machine import StateMachine
from machine.states.scan_state import ScanState

from websocket.utils.messages import ArucoFindMessage, BaseMessage, ErrorMessage


def aruco_handler(msg: ArucoFindMessage, sm: StateMachine):
    try:
        sm.transition_to(ScanState(sm, msg.marker_id))
        return BaseMessage(type="find_aruco_ack")
    except Exception as e:
        return ErrorMessage(code="ARUCO_FINDING_ERROR", message=str(e))
