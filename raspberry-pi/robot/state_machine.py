from .machine.base_state import BaseState
from .machine.states.init_state import InitState
from .motors.motors import Motors
from .utils.debug import get_logger
from .vision.camera import Camera

# Initialize module logger
logger = get_logger("state_machine")


class StateMachine:
    def __init__(self):
        self.motors = Motors()
        self.camera = Camera()

        # State machine properties
        self.current_state: BaseState = InitState()
        self.running = False
        self.previous_state = None

    def start(self):
        """Start the state machine"""
        logger.info("Starting state machine")
        self.running = True
        self.current_state.enter(self)

    def update(self):
        """Called by the main loop to update the state"""
        if not self.running:
            return
            # Essential to prevent enter and exit from running every time, this way only execute runs
        try:
            next_state = self.current_state.execute(self)

            if next_state and next_state != self.current_state:
                self._transition_to(next_state)

        except Exception as e:
            logger.error(f"Error in state {type(self.current_state).__name__}: {e}")

    def _transition_to(self, new_state: BaseState):
        """Handle the transition between states"""
        logger.info(
            f"State transition: {type(self.current_state).__name__} -> {type(new_state).__name__}"
        )
        self.current_state.exit(self)
        self.previous_state = self.current_state
        self.current_state = new_state
        self.current_state.enter(self)

    def stop(self):
        """Stop the state machine"""
        logger.info("Stopping state machine")
        self.running = False
        self.current_state.exit(self)
        self.camera.stop()
        logger.info("State machine stopped successfully")
