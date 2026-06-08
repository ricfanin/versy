# Messages models

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field


class BaseMessage(BaseModel):
    type: str


# incoming message


class MoveMessage(BaseMessage):
    type: Literal["move"] = "move"  # type: ignore[override]
    vx: float
    vy: float
    omega: float


class StopMessage(BaseMessage):
    type: Literal["stop"] = "stop"  # type: ignore[override]


class ArucoFindMessage(BaseMessage):
    type: Literal["find_aruco"] = "find_aruco"  # type: ignore[override]
    marker_id: int
    ml: int


class PourMessage(BaseMessage):
    type: Literal["pour"] = "pour"  # type: ignore[override]
    ml: int


class PourStartMessage(BaseMessage):
    type: Literal["pour_start"] = "pour_start"  # type: ignore[override]


class PourStopMessage(BaseMessage):
    type: Literal["pour_stop"] = "pour_stop"  # type: ignore[override]


# outgoing message


class StatusMessage(BaseMessage):
    type: Literal["status"] = "status"  # type: ignore[override]
    state: str
    battery: int | None = None
    message: str | None = None


class ArucoFoundMessage(BaseMessage):
    type: Literal["aruco_found"] = "aruco_found"  # type: ignore[override]
    marker_id: int


class ArucoLostMessage(BaseMessage):
    type: Literal["aruco_lost"] = "aruco_lost"  # type: ignore[override]
    marker_id: int


class PourCompleteMessage(BaseMessage):
    type: Literal["pour_complete"] = "pour_complete"  # type: ignore[override]
    ml_poured: float


class ErrorMessage(BaseMessage):
    type: Literal["error"] = "error"  # type: ignore[override]
    code: str
    message: str


class JobInfo(BaseModel):
    username: str
    marker_id: int


class RobotStatusMessage(BaseMessage):
    type: Literal["robot_status"] = "robot_status"  # type: ignore[override]
    state: str
    current_job: JobInfo | None = None
    queue: list[JobInfo] = []
    connected_users: list[str] = []


IncomingMessages = Annotated[
    Union[MoveMessage, StopMessage, ArucoFindMessage, PourMessage, PourStartMessage, PourStopMessage],
    Field(discriminator="type"),
]

OutgoingMessages = Annotated[
    Union[StatusMessage, RobotStatusMessage, ArucoFoundMessage, ArucoLostMessage, PourCompleteMessage, ErrorMessage],
    Field(discriminator="type"),
]
