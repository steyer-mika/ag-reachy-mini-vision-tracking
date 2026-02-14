from pathlib import Path
from typing import Any, Dict, TypeVar
import yaml

T = TypeVar("T")


class Config:
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
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

    # Model settings
    @property
    def MODEL_PATH(self) -> Path:
        return Path(self._get("model", "path", default="./models/hand_landmarker.task"))

    # Camera settings
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
    def CAMERA_FRAME_SKIP(self) -> int:
        return self._get("camera", "frame_skip", default=2)

    def reload(self):
        """Reload configuration from file."""
        self._load_config()


# Global config instance (singleton pattern)
_config_instance = None


def get_config(config_path: str = "./src/config/config.yml") -> Config:
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_path)
    return _config_instance
