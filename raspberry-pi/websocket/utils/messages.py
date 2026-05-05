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


class PourMessage(BaseMessage):
    type: Literal["pour"] = "pour"  # type: ignore[override]
    ml: int


# outgoing message


class StatusMessage(BaseMessage):
    type: Literal["status"] = "status"  # type: ignore[override]
    state: str
    battery: int | None = None
    message: str | None = None


class ArucoFoundMessage(BaseMessage):
    type: Literal["aruco_found"] = "aruco_found"  # type: ignore[override]
    marker_id: int


class PourCompleteMessage(BaseMessage):
    type: Literal["pour_complete"] = "pour_complete"  # type: ignore[override]
    ml_poured: float


class ErrorMessage(BaseMessage):
    type: Literal["error"] = "error"  # type: ignore[override]
    code: str
    message: str


IncomingMessages = Annotated[
    Union[MoveMessage, StopMessage, ArucoFindMessage, PourMessage],
    Field(discriminator="type"),
]

OutgoingMessages = Annotated[
    Union[StatusMessage, ArucoFoundMessage, PourCompleteMessage, ErrorMessage],
    Field(discriminator="type"),
]
