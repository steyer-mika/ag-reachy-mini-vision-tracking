from pathlib import Path
from typing import Any, Dict, TypeVar
import yaml
import os

T = TypeVar("T")


class Config:
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}\n"
                f"Please create a config.yml file or specify a valid path."
            )
        with open(self.config_path, "r") as f:
            self._config = yaml.safe_load(f)

    def _get(self, *keys, default: T) -> T:
        value: Any = self._config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, default)
            else:
                return default
        return value

    @property
    def DEV_MODE(self) -> bool:
        return self._get("dev_mode", default=False)

    @property
    def MODEL_PATH(self) -> Path:
        return (
            Path(os.getcwd())
            / "ag_reachy_mini_vision_tracking"
            / "models"
            / "hand_landmarker.task"
        )

    @property
    def HAND_LANDMARKER_MODEL(self) -> str:
        return self._get(
            "mediapipe",
            "hand_landmarker_model",
            default="https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
        )

    @property
    def FACE_MODEL_PATH(self) -> Path:
        return (
            Path(os.getcwd())
            / "ag_reachy_mini_vision_tracking"
            / "models"
            / "blaze_face_short_range.tflite"
        )

    @property
    def FACE_MODEL_URL(self) -> str:
        return self._get(
            "mediapipe",
            "face_detector_model",
            default="https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite",
        )

    @property
    def CAMERA_INDICES(self) -> list[int]:
        return self._get("camera", "indices", default=[0, 1, 2])

    @property
    def CAMERA_WIDTH(self) -> int:
        return self._get("camera", "width", default=640)

    @property
    def CAMERA_HEIGHT(self) -> int:
        return self._get("camera", "height", default=480)

    @property
    def TARGET_FPS(self) -> int:
        return self._get("camera", "target_fps", default=30)

    @property
    def CAMERA_FLIP_HORIZONTAL(self) -> bool:
        return self._get("camera", "flip_horizontal", default=True)

    @property
    def MAX_HANDS(self) -> int:
        return self._get("tracking", "max_hands", default=2)

    @property
    def MIN_DETECTION_CONFIDENCE(self) -> float:
        return self._get("tracking", "min_detection_confidence", default=0.5)

    @property
    def MIN_TRACKING_CONFIDENCE(self) -> float:
        return self._get("tracking", "min_tracking_confidence", default=0.5)

    @property
    def TRACKING_LOST_THRESHOLD(self) -> int:
        """Consecutive frames without a face before PID resets."""
        return self._get("autonomous_tracking", "lost_threshold", default=10)

    @property
    def TRACKING_KP_YAW(self) -> float:
        return self._get("autonomous_tracking", "pid", "yaw", "kp", default=30.0)

    @property
    def TRACKING_KI_YAW(self) -> float:
        return self._get("autonomous_tracking", "pid", "yaw", "ki", default=0.0)

    @property
    def TRACKING_KD_YAW(self) -> float:
        return self._get("autonomous_tracking", "pid", "yaw", "kd", default=5.0)

    @property
    def TRACKING_KP_PITCH(self) -> float:
        return self._get("autonomous_tracking", "pid", "pitch", "kp", default=20.0)

    @property
    def TRACKING_KI_PITCH(self) -> float:
        return self._get("autonomous_tracking", "pid", "pitch", "ki", default=0.0)

    @property
    def TRACKING_KD_PITCH(self) -> float:
        return self._get("autonomous_tracking", "pid", "pitch", "kd", default=3.0)

    @property
    def HEAD_PITCH_MIN(self) -> float:
        return self._get("robot", "head", "pitch_min", default=-20.0)

    @property
    def HEAD_PITCH_MAX(self) -> float:
        return self._get("robot", "head", "pitch_max", default=20.0)

    @property
    def HEAD_YAW_AMPLITUDE(self) -> float:
        """Maximum yaw angle (degrees). Also used as the PID output limit."""
        return self._get("robot", "head", "yaw_amplitude", default=30.0)

    @property
    def ANTENNA_AMPLITUDE(self) -> float:
        """Fixed oscillation amplitude in degrees (no longer finger-driven)."""
        return self._get("robot", "antenna", "amplitude", default=20.0)

    @property
    def ANTENNA_FREQUENCY(self) -> float:
        return self._get("robot", "antenna", "frequency", default=0.5)

    @property
    def CONTROL_LOOP_RATE(self) -> float:
        return self._get("robot", "control_loop_rate", default=0.02)

    @property
    def API_HOST(self) -> str:
        return self._get("api", "host", default="0.0.0.0")

    @property
    def API_PORT(self) -> int:
        return self._get("api", "port", default=8042)


_config_instance = None


def get_config(config_path: Path) -> Config:
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_path)
    return _config_instance
