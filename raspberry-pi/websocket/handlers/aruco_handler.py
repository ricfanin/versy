from machine.state_machine import Job, StateMachine

from websocket.utils.messages import ArucoFindMessage, BaseMessage, ErrorMessage


def aruco_handler(msg: ArucoFindMessage, sm: StateMachine, username: str):
    try:
        sm.enqueue(Job(username=username, marker_id=msg.marker_id, ml=msg.ml))
        return BaseMessage(type="find_aruco_queued")
    except Exception as e:
        return ErrorMessage(code="ARUCO_FINDING_ERROR", message=str(e))
