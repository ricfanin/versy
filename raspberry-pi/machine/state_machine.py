from .base_state import BaseState
from .states.init_state import InitState
from robot.robot import Robot
from utils.debug import get_logger

logger = get_logger("state_machine")


class StateMachine:
    def __init__(self):
        self.robot = Robot()

        # State machine properties
        self.current_state: BaseState = InitState(self)
        self.running = False

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
                self._transition_to(next_state)

        except Exception as e:
            logger.error(f"Error in state {type(self.current_state).__name__}: {e}")
        finally:
            return True

    def _transition_to(self, new_state: BaseState):
        """Handle the transition between states"""
        logger.info(
            f"State transition: {type(self.current_state).__name__} -> {type(new_state).__name__}"
        )
        self.current_state.exit()
        self.current_state = new_state
        self.current_state.enter()

    def stop(self):
        """Stop the state machine"""
        if self.running:
            logger.info("Stopping state machine")
            self.running = False
            self.current_state.exit()
            self.robot.stop()
            logger.info("State machine stopped successfully")
