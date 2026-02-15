import threading
import os
import warnings

# Suppress TensorFlow/MediaPipe warnings
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"  # Suppress TensorFlow warnings
warnings.filterwarnings("ignore", category=UserWarning)

from reachy_mini import ReachyMini, ReachyMiniApp
import time
from pydantic import BaseModel
from pathlib import Path

from .config.config_loader import get_config
from .vision.video_processor import VideoProcessor
from .app_state import AppState


class AgReachyMiniVisionTracking(ReachyMiniApp):
    custom_app_url: str | None = "http://0.0.0.0:8042"
    request_media_backend: str | None = None

    def __init__(self):
        super().__init__()

        # Load config
        self.config = get_config(
            Path(__file__).resolve().parents[0] / "config" / "config.yml"
        )

        # Shared state
        self.shared_state = AppState()

        # Video processor
        self.video_processor: VideoProcessor | None = None

    def _on_finger_count_update(self, count: int) -> None:
        self.shared_state.set_finger_count(count)

    def _setup_api_endpoints(self) -> None:
        if not self.settings_app:
            return None

        class AntennaState(BaseModel):
            enabled: bool

        @self.settings_app.post("/antennas")
        def update_antennas_state(state: AntennaState):
            self.shared_state.set_antennas_enabled(state.enabled)
            return {"antennas_enabled": state.enabled}

        @self.settings_app.post("/play_sound")
        def request_sound_play():
            self.shared_state.request_sound_play()
            return {"status": "requested"}

        @self.settings_app.get("/finger_count")
        def get_finger_count():
            return {"finger_count": self.shared_state.get_finger_count()}

    def run(self, reachy_mini: ReachyMini, stop_event: threading.Event):
        self._setup_api_endpoints()

        self.video_processor = VideoProcessor(
            self.config, on_finger_count_update=self._on_finger_count_update
        )
        self.video_processor.start()

        # Main control loop
        while not stop_event.is_set():
            try:
                # Get current state
                finger_count = self.shared_state.get_finger_count()
                antennas_enabled = self.shared_state.get_antennas_enabled()

                print(
                    f"Finger Count: {finger_count}, Antennas Enabled: {antennas_enabled}"
                )

                # Handle sound play request
                if self.shared_state.is_sound_play_requested():
                    print("Playing sound...")
                    reachy_mini.media.play_sound("wake_up.wav")
                    self.shared_state.clear_sound_play_request()

                # Sleep for control loop rate
                time.sleep(self.config.CONTROL_LOOP_RATE)

            except Exception as e:
                print(f"Error in control loop: {e}")
                time.sleep(0.1)

        # Cleanup
        if self.video_processor:
            self.video_processor.stop()


if __name__ == "__main__":
    app = AgReachyMiniVisionTracking()
    try:
        app.wrapped_run()
    except KeyboardInterrupt:
        app.stop()
