from pathlib import Path
from typing import Any, Dict, List, Tuple, TypeVar
import yaml

T = TypeVar("T")


class Config:
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
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
    def MODEL_PATH(self) -> Path:
        return Path(self._get("model", "path", default="./models/hand_landmarker.task"))

    @property
    def WINDOW_HANDLE(self) -> str:
        return self._get(
            "camera", "window_handle", default="Reachy Mini | Vision and Tracking"
        )

    @property
    def CAMERA_INDEX(self) -> int:
        return self._get("camera", "index", default=0)

    @property
    def CAMERA_WIDTH(self) -> int:
        return self._get("camera", "width", default=1280)

    @property
    def CAMERA_HEIGHT(self) -> int:
        return self._get("camera", "height", default=720)

    @property
    def TARGET_FPS(self) -> int:
        return self._get("camera", "target_fps", default=30)

    @property
    def WEBSOCKET_PORT(self) -> int:
        return self._get("websocket", "port", default=8765)

    @property
    def WEBSOCKET_HOST(self) -> str:
        return self._get("websocket", "host", default="0.0.0.0")

    @property
    def WEBSOCKET_STARTUP_DELAY(self) -> float:
        return self._get("websocket", "startup_delay", default=1.0)

    @property
    def MAX_HANDS(self) -> int:
        return self._get("tracking", "max_hands", default=2)

    @property
    def PROCESS_EVERY_N_FRAMES(self) -> int:
        return self._get("tracking", "process_every_n_frames", default=2)

    @property
    def SMOOTHING_ALPHA(self) -> float:
        return self._get("tracking", "smoothing_alpha", default=0.3)

    @property
    def REACTION_DELAY(self) -> float:
        return self._get("robot", "reaction_delay", default=0.5)

    @property
    def REACTION_COOLDOWN(self) -> float:
        return self._get("robot", "reaction_cooldown", default=1.0)

    @property
    def GESTURE_DURATION(self) -> float:
        return self._get("robot", "gesture_duration", default=0.5)

    @property
    def ANTENNA_DURATION(self) -> float:
        return self._get("robot", "antenna_duration", default=0.3)

    # ==========================================================================
    # Methods
    # ==========================================================================

    def reload(self) -> None:
        """Reload configuration from file (useful for hot-reloading)."""


_config_instance = None


def get_config(config_path: str = "./src/config/config.yml") -> Config:
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_path)
    return _config_instance
