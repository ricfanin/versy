from websocket.utils.messages import ArucoFindMessage, ArucoFoundMessage, ErrorMessage
from websocket.interfaces.aruco_interface import search_aruco
from pydantic import TypeAdapter
from machine.state_machine import StateMachine
from machine.states.scan_state import ScanState


def aruco_handler(msg: ArucoFindMessage, sm: StateMachine):
    try:
        # distance, angle = search_aruco(marker_id=msg.marker_id) # interfaccia con robot
        sm.transition_to(ScanState(sm, msg.marker_id))
        response = ArucoFoundMessage(
            marker_id=msg.marker_id, 
            distance_cm=0, 
            angle_deg=0
        )
    except Exception as e:
        response = ErrorMessage(
            code="ARUCO_FINDING_ERROR",
            message=str(e)
        )

    return response 
    