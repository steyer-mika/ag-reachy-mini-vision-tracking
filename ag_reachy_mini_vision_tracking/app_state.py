import threading
from typing import Any


class AppState:
    def __init__(self):
        self._lock = threading.Lock()
        self._state: dict[str, Any] = {
            "finger_count": 0,
            "antennas_enabled": True,
            "sound_play_requested": False,
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
