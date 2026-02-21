import threading
import time
from typing import Callable, List, Dict, Any, Optional

from ..config.config_loader import Config
from .camera_handler import CameraHandler
from .hand_detector import HandDetector
from .face_tracker import FaceTracker, TrackingResult


class VideoProcessor:
    def __init__(
        self,
        config: Config,
        on_finger_count_update: Callable[[int, List[Dict[str, Any]]], None],
        on_tracking_update: Callable[[TrackingResult], None],
        # Dev-mode only: (frame_rgb, raw_hand_result, tracking_result, total_fingers)
        on_dev_frame: Optional[Callable] = None,
    ):
        self.config = config
        self.on_finger_count_update = on_finger_count_update
        self.on_tracking_update = on_tracking_update
        self.on_dev_frame = on_dev_frame

        self.camera_handler: Optional[CameraHandler] = None
        self.hand_detector: Optional[HandDetector] = None
        self.face_tracker: Optional[FaceTracker] = None

        self.thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

    def start(self) -> None:
        if self.thread is not None and self.thread.is_alive():
            print("Video processor already running")
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._process_loop, daemon=True)
        self.thread.start()
        print("Video processing thread started")

    def stop(self, timeout: float = 2.0) -> None:
        if self.thread is None:
            return
        print("Stopping video processing thread…")
        self.stop_event.set()
        self.thread.join(timeout=timeout)
        if self.camera_handler:
            self.camera_handler.release()
        if self.hand_detector:
            self.hand_detector.close()
        if self.face_tracker:
            self.face_tracker.close()
        print("Video processing thread stopped")

    def _process_loop(self) -> None:
        try:
            self.camera_handler = CameraHandler(self.config)
            self.hand_detector = HandDetector(self.config)
            self.face_tracker = FaceTracker(self.config)
        except Exception as e:
            print(f"Error initializing video processing: {e}")
            return

        if not self.camera_handler.is_opened():
            print("Warning: Camera not available. All vision features disabled.")
            return

        frame_delay = 1.0 / self.config.TARGET_FPS
        prev_time = time.time()

        while not self.stop_event.is_set():
            try:
                success, frame = self.camera_handler.read_frame()
                if not success or frame is None:
                    print("Failed to grab frame")
                    time.sleep(0.1)
                    continue

                now = time.time()
                dt = now - prev_time
                prev_time = now
                timestamp_ms = int(now * 1000)

                total_fingers, raw_hand_result, hands_data = (
                    self.hand_detector.detect_hands(frame, timestamp_ms)
                )
                self.on_finger_count_update(total_fingers, hands_data)

                tracking_result = self.face_tracker.update(frame, timestamp_ms, dt)
                self.on_tracking_update(tracking_result)

                if self.on_dev_frame is not None:
                    self.on_dev_frame(
                        frame, raw_hand_result, tracking_result, total_fingers
                    )

                time.sleep(frame_delay)

            except Exception as e:
                print(f"Error in video processing frame: {e}")
                time.sleep(0.1)
