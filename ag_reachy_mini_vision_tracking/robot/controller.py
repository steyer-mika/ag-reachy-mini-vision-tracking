import numpy as np
import time
from reachy_mini.utils import create_head_pose

from ..config.config_loader import Config


class RobotController:
    def __init__(self, config: Config, start_time: float):
        self.config = config
        self.start_time = start_time

    def calculate_head_pose(self, finger_count: int, elapsed_time: float) -> np.ndarray:
        # Pitch based on finger count
        # 0 fingers: look down, 5 fingers: neutral, 10 fingers: look up
        pitch_deg = (finger_count - 5) * self.config.HEAD_PITCH_SCALE
        pitch_deg = np.clip(
            pitch_deg, self.config.HEAD_PITCH_MIN, self.config.HEAD_PITCH_MAX
        )

        # Add gentle sway in yaw
        yaw_deg = self.config.HEAD_YAW_AMPLITUDE * np.sin(
            2.0 * np.pi * self.config.HEAD_YAW_FREQUENCY * elapsed_time
        )

        return create_head_pose(yaw=yaw_deg, pitch=pitch_deg, degrees=True)

    def calculate_antenna_positions(
        self, finger_count: int, elapsed_time: float, enabled: bool = True
    ) -> np.ndarray:
        if not enabled:
            return np.array([0.0, 0.0])

        # Amplitude increases with finger count
        amp_deg = min(
            finger_count * self.config.ANTENNA_SCALE, self.config.ANTENNA_MAX_AMPLITUDE
        )

        # Oscillate antennas
        a = amp_deg * np.sin(2.0 * np.pi * self.config.ANTENNA_FREQUENCY * elapsed_time)
        antennas_deg = np.array([a, -a])

        return np.deg2rad(antennas_deg)

    def get_elapsed_time(self) -> float:
        return time.time() - self.start_time
