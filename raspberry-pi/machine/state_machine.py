import threading
from collections import deque
from dataclasses import dataclass
from typing import Callable, Optional

from .base_state import BaseState
from .states.init_state import InitState
from robot.robot import Robot
from utils.debug import get_logger
from websocket.utils.messages import BaseMessage

logger = get_logger("state_machine")


@dataclass
class Job:
    username: str
    marker_id: int
    ml: int


class StateMachine:
    def __init__(self):
        self.robot = Robot()

        # State machine properties
        self.current_state: BaseState = InitState(self)
        self.running = False
        self.publisher: Callable[[BaseMessage], None] = lambda msg: None
        self.status_changed: Callable[[], None] = lambda: None

        # Job queue
        self.queue: deque[Job] = deque()
        self.queue_lock = threading.Lock()
        self.current_job: Optional[Job] = None

    def publish(self, message: BaseMessage) -> None:
        self.publisher(message)

    def enqueue(self, job: Job) -> int:
        """Append a job to the queue, returns its position (1-based)."""
        with self.queue_lock:
            self.queue.append(job)
            position = len(self.queue)
        self.status_changed()
        return position

    def dequeue(self) -> Optional[Job]:
        with self.queue_lock:
            if self.queue:
                return self.queue.popleft()
            return None

    def clear_queue(self) -> None:
        with self.queue_lock:
            self.queue.clear()
        self.status_changed()

    def get_queue_snapshot(self) -> list[Job]:
        with self.queue_lock:
            return list(self.queue)

    def start(self):
        """Start the state machine"""
        logger.info("Starting state machine")
        self.running = True
        self.current_state.enter()

    def update(self):
        """Called by the main loop to update the state"""
        if not self.running:
            return False
            # Essential to prevent enter and exit from running every time, this way only execute runs
        try:
            next_state = self.current_state.execute()

            if next_state and next_state != self.current_state:
                self.transition_to(next_state)

        except Exception as e:
            logger.error(f"Error in state {type(self.current_state).__name__}: {e}")
        finally:
            return True

    def transition_to(self, new_state: BaseState):
        """Handle the transition between states"""
        logger.info(
            f"State transition: {type(self.current_state).__name__} -> {type(new_state).__name__}"
        )
        self.current_state.exit()
        self.current_state = new_state
        self.current_state.enter()
        self.status_changed()

    def stop(self):
        """Stop the state machine"""
        if self.running:
            logger.info("Stopping state machine")
            self.running = False
            self.current_state.exit()
            self.robot.stop()
            logger.info("State machine stopped successfully")
