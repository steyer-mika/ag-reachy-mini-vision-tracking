import threading
import os
import warnings
import asyncio
import queue

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
warnings.filterwarnings("ignore", category=UserWarning)

from reachy_mini import ReachyMini, ReachyMiniApp
import time
from pathlib import Path
from typing import List, Dict, Any

from .config.config_loader import get_config
from .vision.video_processor import VideoProcessor
from .vision.face_tracker import TrackingResult
from .app_state import AppState
from .robot.controller import RobotController
from .api.websocket.connection_manager import ConnectionManager
from .api.endpoints import setup_api_endpoints


class AgReachyMiniVisionTracking(ReachyMiniApp):
    custom_app_url: str | None = "http://0.0.0.0:8042"
    request_media_backend: str | None = None

    def __init__(self):
        super().__init__()

        self.config = get_config(
            Path(__file__).resolve().parents[0] / "config" / "config.yml"
        )

        self.shared_state = AppState()
        self.connection_manager = ConnectionManager()
        self.event_loop_ref: list = [None]

        self.video_processor: VideoProcessor | None = None
        self.robot_controller: RobotController | None = None

        self._latest_tracking: TrackingResult | None = None
        self._tracking_lock = threading.Lock()

        # Dev-mode: frames are produced on the vision thread but cv2.imshow
        # must be called from the main thread, so we pass them via a queue.
        self._dev_frame_queue: queue.Queue = queue.Queue(maxsize=2)

    # ── Dev-mode detection ───────────────────────────────────────────────

    def _is_dev_mode(self, reachy_mini: ReachyMini) -> bool:
        if self.config.DEV_MODE:
            return True
        if getattr(reachy_mini, "is_virtual", False):
            print("reachy_mini.is_virtual=True → DEV_MODE enabled automatically")
            return True
        if os.environ.get("REACHY_DEV", "").lower() in ("1", "true", "yes"):
            return True
        return False

    def _on_finger_count_update(
        self, count: int, hands_data: List[Dict[str, Any]]
    ) -> None:
        self.shared_state.set_finger_count(count)
        self.shared_state.set_hands_data(hands_data)

        event_loop = self.event_loop_ref[0]
        if event_loop and not event_loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                self.connection_manager.broadcast(
                    {
                        "type": "finger_count",
                        "finger_count": count,
                        "hands_detected": len(hands_data),
                        "hands": hands_data,
                    }
                ),
                event_loop,
            )

    def _on_tracking_update(self, result: TrackingResult) -> None:
        with self._tracking_lock:
            self._latest_tracking = result

        event_loop = self.event_loop_ref[0]
        if event_loop and not event_loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                self.connection_manager.broadcast(
                    {
                        "type": "tracking",
                        "tracking": result.tracking,
                        "faces_detected": len(result.faces),
                        "dx": round(result.dx, 3),
                        "dy": round(result.dy, 3),
                    }
                ),
                event_loop,
            )

    def _on_dev_frame(self, frame, raw_hand_result, tracking_result, total_fingers):
        try:
            self._dev_frame_queue.put_nowait(
                (frame, raw_hand_result, tracking_result, total_fingers)
            )
        except queue.Full:
            pass  # drop frame rather than block the vision thread

    def _get_latest_tracking(self) -> TrackingResult | None:
        with self._tracking_lock:
            return self._latest_tracking

    def _setup_api_endpoints(self) -> None:
        if not self.settings_app:
            return
        setup_api_endpoints(
            self.settings_app,
            self.shared_state,
            self.connection_manager,
            self.event_loop_ref,
        )

    def run(self, reachy_mini: ReachyMini, stop_event: threading.Event):
        self._setup_api_endpoints()

        dev_mode = self._is_dev_mode(reachy_mini)
        if dev_mode:
            print("=" * 50)
            print("  DEV MODE active - cv2 debug window will open")
            print("  Press 'q' in the window to quit")
            print("=" * 50)

        start_time = time.time()
        self.robot_controller = RobotController(self.config, start_time)

        self.video_processor = VideoProcessor(
            self.config,
            on_finger_count_update=self._on_finger_count_update,
            on_tracking_update=self._on_tracking_update,
            on_dev_frame=self._on_dev_frame if dev_mode else None,
        )
        self.video_processor.start()

        visualizer = None
        if dev_mode:
            from .debug.dev_visualizer import DevVisualizer

            visualizer = DevVisualizer(self.config)
            visualizer.open()

        try:
            while not stop_event.is_set():

                try:
                    tracking_result = self._get_latest_tracking()
                    antennas_enabled = self.shared_state.get_antennas_enabled()
                    elapsed_time = self.robot_controller.get_elapsed_time()

                    head_pose = self.robot_controller.calculate_head_pose(
                        tracking_result
                    )
                    antennas = self.robot_controller.calculate_antenna_positions(
                        elapsed_time, antennas_enabled
                    )

                    if self.shared_state.is_sound_play_requested():
                        print("Playing sound…")
                        reachy_mini.media.play_sound("wake_up.wav")
                        self.shared_state.clear_sound_play_request()

                    reachy_mini.set_target(head=head_pose, antennas=antennas)

                except Exception as e:
                    print(f"Error in control loop: {e}")

                if visualizer is not None:
                    try:
                        frame, raw_hand, tracking, total = (
                            self._dev_frame_queue.get_nowait()
                        )
                        annotated = visualizer.annotate(
                            frame, raw_hand, tracking, total
                        )
                        if visualizer.show(annotated):
                            print("Dev window closed by user - stopping.")
                            stop_event.set()
                            break
                    except queue.Empty:
                        import cv2

                        cv2.waitKey(1)

                time.sleep(self.config.CONTROL_LOOP_RATE)

        finally:
            if visualizer is not None:
                visualizer.close()
            if self.video_processor:
                self.video_processor.stop()


if __name__ == "__main__":
    app = AgReachyMiniVisionTracking()
    try:
        app.wrapped_run()
    except KeyboardInterrupt:
        app.stop()
