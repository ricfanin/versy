import time

from robot.state_machine import StateMachine
from robot.utils.debug import get_logger

# Initialize module logger
logger = get_logger("main")


def main():
    """Entry point to test the robot"""
    try:
        logger.info("Initializing robot system")
        state_machine = StateMachine()

        logger.info("Starting state machine")
        state_machine.start()

        # Main loop
        logger.info("Starting main loop at 20Hz")
        loop_count = 0
        while True:
            state_machine.update()

            # Log heartbeat every 5 seconds (100 iterations at 20Hz)
            if loop_count % 100 == 0:
                logger.debug(f"Main loop heartbeat - iteration {loop_count}")

            loop_count += 1
            time.sleep(0.05)  # 20Hz update rate

    except KeyboardInterrupt:
        logger.warning("Shutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error occurred: {e}")
    finally:
        logger.info("Cleaning up resources")
        state_machine.stop()
        logger.info("Shutdown completed")


if __name__ == "__main__":
    main()
