import time

from robot.state_machine import StateMachine
from robot.utils.debug import get_logger

logger = get_logger("main")


def main():
    """Entry point to test the robot"""
    state_machine = None
    try:
        logger.info("Initializing robot system")
        state_machine = StateMachine()

        logger.info("Starting state machine")
        state_machine.start()

        logger.info("Starting main loop at 20Hz")
        while state_machine.update():
            time.sleep(0.05)  # 20Hz update rate

    except KeyboardInterrupt:
        logger.warning("Shutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error occurred: {e}")
    finally:
        logger.info("Cleaning up resources")
        if state_machine is not None:
            state_machine.stop()
        logger.info("Shutdown completed")


if __name__ == "__main__":
    main()
