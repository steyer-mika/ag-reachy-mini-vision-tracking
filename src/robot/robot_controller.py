import asyncio
import time
from typing import Optional
from reachy_mini import ReachyMini

from lib.logger import Logger


class RobotController:
    def __init__(self):
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

    def startup_gesture(self):
        if not self.connected or not self.robot:
            self.logger.warning("Robot not connected, skipping startup gesture")
            return

        try:
            self.logger.info("Performing startup gesture...")

            # Wave the antennas in a greeting pattern
            self.robot.goto_target(antennas=[0.5, -0.5], duration=0.5)
            time.sleep(0.5)

            self.robot.goto_target(antennas=[-0.5, 0.5], duration=0.5)
            time.sleep(0.5)

            self.robot.goto_target(antennas=[0.5, -0.5], duration=0.5)
            time.sleep(0.5)

            self.robot.goto_target(antennas=[0, 0], duration=0.5)
            time.sleep(0.5)

            self.logger.info("Startup gesture complete!")

        except Exception as e:
            self.logger.error(f"Error performing startup gesture: {e}")

    def react_to_finger_count(self, finger_count: int):
        if not self.connected or not self.robot:
            return

        try:
            # Map finger count to antenna positions
            # 0 fingers: antennas down
            # 5 fingers: antennas up
            # 10 fingers: antennas fully up

            if finger_count == 0:
                left_antenna = 0.0
                right_antenna = 0.0
            elif finger_count <= 5:
                # Gradually raise antennas
                position = finger_count / 5.0
                left_antenna = position * 0.5
                right_antenna = position * 0.5
            else:
                # Both hands raised - antennas go opposite directions
                position = (finger_count - 5) / 5.0
                left_antenna = 0.5 + position * 0.3
                right_antenna = -(0.5 + position * 0.3)

            self.robot.goto_target(antennas=[left_antenna, right_antenna], duration=0.3)

        except Exception as e:
            self.logger.error(f"Error reacting to finger count: {e}")
