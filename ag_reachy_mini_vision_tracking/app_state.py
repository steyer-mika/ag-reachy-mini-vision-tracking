import threading
from typing import Any, Optional


class AppState:
    def __init__(self):
        self._lock = threading.Lock()
        self._state: dict[str, Any] = {
            "finger_count": 0,
            "antennas_enabled": True,
            "sound_play_requested": False,
            "robot_control_command": None,
            "hands_data": [],
        }

    def get_finger_count(self) -> int:
        with self._lock:
            return self._state["finger_count"]

    def set_finger_count(self, count: int) -> None:
        with self._lock:
            self._state["finger_count"] = count

    def get_antennas_enabled(self) -> bool:
        with self._lock:
            return self._state["antennas_enabled"]

    def set_antennas_enabled(self, enabled: bool) -> None:
        with self._lock:
            self._state["antennas_enabled"] = enabled

    def is_sound_play_requested(self) -> bool:
        with self._lock:
            return self._state["sound_play_requested"]

    def request_sound_play(self) -> None:
        with self._lock:
            self._state["sound_play_requested"] = True

    def clear_sound_play_request(self) -> None:
        with self._lock:
            self._state["sound_play_requested"] = False

    def set_robot_control_command(self, direction: str) -> None:
        with self._lock:
            self._state["robot_control_command"] = direction

    def get_robot_control_command(self) -> Optional[str]:
        with self._lock:
            command = self._state["robot_control_command"]
            self._state["robot_control_command"] = None
            return command

    def set_hands_data(self, hands_data: list) -> None:
        with self._lock:
            self._state["hands_data"] = hands_data

    def get_hands_data(self) -> list:
        with self._lock:
            return self._state["hands_data"].copy()
