import time
from typing import Optional

from reachy_mini import ReachyMini

from config.config_loader import Config
from lib.logger import Logger


class RobotController:
    def __init__(self, config: Config):
        self.config = config
        self.robot: Optional[ReachyMini] = None
        self.logger = Logger(RobotController.__name__).get()
        self.connected = False

    def __enter__(self):
        try:
            self.robot = ReachyMini()
            self.robot.__enter__()
            self.connected = True
            self.logger.info("Successfully connected to Reachy Mini!")
            return self
        except Exception as e:
            # Graceful degradation: continue without robot if connection fails
            self.logger.error(f"Failed to connect to Reachy Mini: {e}")
            self.logger.warning("Continuing without robot connection...")
            self.connected = False
            return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.robot:
            try:
                self.robot.__exit__(exc_type, exc_val, exc_tb)
                self.logger.info("Disconnected from Reachy Mini")
            except Exception as e:
                self.logger.error(f"Error disconnecting from robot: {e}")

    def startup_gesture(self) -> None:
        if not self.connected or not self.robot:
            self.logger.warning("Robot not connected, skipping startup gesture")
            return

        try:
            self.logger.info("Performing startup gesture...")
            duration = self.config.GESTURE_DURATION

            # Wave pattern: alternating left-right antenna tilts
            self.robot.goto_target(antennas=[0.5, -0.5], duration=duration)
            time.sleep(duration)

            self.robot.goto_target(antennas=[-0.5, 0.5], duration=duration)
            time.sleep(duration)

            self.robot.goto_target(antennas=[0.5, -0.5], duration=duration)
            time.sleep(duration)

            # Return to neutral position
            self.robot.goto_target(antennas=[0, 0], duration=duration)
            time.sleep(duration)

            self.logger.info("Startup gesture complete!")

        except Exception as e:
            self.logger.error(f"Error performing startup gesture: {e}")

    def react_to_finger_count(self, finger_count: int) -> None:
        if not self.connected or not self.robot:
            return

        try:
            if finger_count == 0:
                # No fingers: neutral resting position
                left_antenna = 0.0
                right_antenna = 0.0
            elif finger_count <= 5:
                # One hand (1-5 fingers): both antennas rise together
                # Linear interpolation: 1 finger = 10% raised, 5 fingers = 50% raised
                position = finger_count / 5.0  # Normalize to 0.0-1.0
                left_antenna = position * 0.5
                right_antenna = position * 0.5
            else:
                # Two hands (6-10 fingers): antennas spread apart
                # Creates an excited/celebratory pose
                # Additional fingers beyond 5 increase the spread
                extra_position = (finger_count - 5) / 5.0  # 0.0-1.0 for fingers 6-10
                left_antenna = 0.5 + extra_position * 0.3  # Left goes more positive
                right_antenna = -(0.5 + extra_position * 0.3)  # Right goes negative

            self.robot.goto_target(
                antennas=[left_antenna, right_antenna],
                duration=self.config.ANTENNA_DURATION,
            )

        except Exception as e:
            self.logger.error(f"Error reacting to finger count: {e}")
