import threading
import os
import warnings
import asyncio

# Suppress TensorFlow/MediaPipe warnings
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"  # Suppress TensorFlow warnings
warnings.filterwarnings("ignore", category=UserWarning)

from reachy_mini import ReachyMini, ReachyMiniApp
import time
from pathlib import Path

from .config.config_loader import get_config
from .vision.video_processor import VideoProcessor
from .app_state import AppState
from .robot.controller import RobotController
from .api.websocket.connection_manager import ConnectionManager
from .api.endpoints import setup_api_endpoints


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

        # WebSocket connection manager
        self.connection_manager = ConnectionManager()
        self.event_loop_ref = [None]  # Mutable reference for event loop

        # Video processor
        self.video_processor: VideoProcessor | None = None
        self.robot_controller: RobotController | None = None

    def _on_finger_count_update(self, count: int) -> None:
        self.shared_state.set_finger_count(count)
        # Broadcast to all connected WebSocket clients from a different thread
        event_loop = self.event_loop_ref[0]
        if event_loop and not event_loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                self.connection_manager.broadcast(
                    {"type": "finger_count", "finger_count": count}
                ),
                event_loop,
            )

    def _setup_api_endpoints(self) -> None:
        if not self.settings_app:
            return None

        setup_api_endpoints(
            self.settings_app,
            self.shared_state,
            self.connection_manager,
            self.event_loop_ref,
        )

    def run(self, reachy_mini: ReachyMini, stop_event: threading.Event):
        self._setup_api_endpoints()

        start_time = time.time()
        self.robot_controller = RobotController(self.config, start_time)

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
                elapsed_time = self.robot_controller.get_elapsed_time()

                head_pose = self.robot_controller.calculate_head_pose(
                    finger_count, elapsed_time
                )

                antennas = self.robot_controller.calculate_antenna_positions(
                    finger_count, elapsed_time, antennas_enabled
                )

                # Handle sound play request
                if self.shared_state.is_sound_play_requested():
                    print("Playing sound...")
                    reachy_mini.media.play_sound("wake_up.wav")
                    self.shared_state.clear_sound_play_request()

                reachy_mini.set_target(
                    head=head_pose,
                    antennas=antennas,
                )

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
