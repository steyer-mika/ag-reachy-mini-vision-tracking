import numpy as np
import time
from reachy_mini.utils import create_head_pose

from ..config.config_loader import Config
from ..vision.face_tracker import TrackingResult


class RobotController:
    def __init__(self, config: Config, start_time: float):
        self.config = config
        self.start_time = start_time

        # Accumulated head angles - updated each tick via PID corrections.
        # Starting at neutral so the head does not jerk on boot.
        self._current_yaw_deg: float = 0.0
        self._current_pitch_deg: float = 0.0

    # ------------------------------------------------------------------ #
    # Head pose
    # ------------------------------------------------------------------ #

    def calculate_head_pose(
        self,
        tracking_result: TrackingResult | None,
    ) -> np.ndarray:
        if tracking_result is not None and tracking_result.tracking:
            yaw_correction = getattr(tracking_result, "yaw_correction_deg", 0.0)
            pitch_correction = getattr(tracking_result, "pitch_correction_deg", 0.0)

            self._current_yaw_deg += yaw_correction
            self._current_pitch_deg += pitch_correction

            self._current_yaw_deg = float(
                np.clip(
                    self._current_yaw_deg,
                    -self.config.HEAD_YAW_AMPLITUDE,
                    self.config.HEAD_YAW_AMPLITUDE,
                )
            )
            self._current_pitch_deg = float(
                np.clip(
                    self._current_pitch_deg,
                    self.config.HEAD_PITCH_MIN,
                    self.config.HEAD_PITCH_MAX,
                )
            )

        return create_head_pose(
            yaw=self._current_yaw_deg,
            pitch=self._current_pitch_deg,
            degrees=True,
        )

    # ------------------------------------------------------------------ #
    # Antennas
    # ------------------------------------------------------------------ #

    def calculate_antenna_positions(
        self,
        elapsed_time: float,
        enabled: bool = True,
    ) -> np.ndarray:
        if not enabled:
            return np.array([0.0, 0.0])

        a = self.config.ANTENNA_AMPLITUDE * np.sin(
            2.0 * np.pi * self.config.ANTENNA_FREQUENCY * elapsed_time
        )
        return np.deg2rad(np.array([a, -a]))

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def get_elapsed_time(self) -> float:
        return time.time() - self.start_time
