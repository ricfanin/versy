from src.utils.messages import ArucoFindMessage, ArucoFoundMessage, ErrorMessage
from src.interfaces.aruco_interface import search_aruco
from pydantic import TypeAdapter


def aruco_handler(msg: ArucoFindMessage):
    try:
        distance, angle = search_aruco(marker_id=msg.marker_id) # interfaccia con robot
        response = ArucoFoundMessage(
            marker_id=msg.marker_id, 
            distance_cm=distance, 
            angle_deg=angle
        )
    except Exception as e:
        response = ErrorMessage(
            code="ARUCO_FINDING_ERROR",
            message=str(e)
        )

    return response 
    