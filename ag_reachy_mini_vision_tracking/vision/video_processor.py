"""Video processing thread for hand tracking."""

import threading
import time
from typing import Callable

from ..config.config_loader import Config
from .camera_handler import CameraHandler
from .hand_detector import HandDetector


class VideoProcessor:
    def __init__(self, config: Config, on_finger_count_update: Callable[[int], None]):
        self.config = config
        self.on_finger_count_update = on_finger_count_update

        self.camera_handler: CameraHandler | None = None
        self.hand_detector: HandDetector | None = None
        self.thread: threading.Thread | None = None
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

        print("Stopping video processing thread...")
        self.stop_event.set()
        self.thread.join(timeout=timeout)

        # Cleanup
        if self.camera_handler:
            self.camera_handler.release()
        if self.hand_detector:
            self.hand_detector.close()

        print("Video processing thread stopped")

    def _process_loop(self) -> None:
        try:
            # Initialize camera and detector
            self.camera_handler = CameraHandler(self.config)
            self.hand_detector = HandDetector(self.config)

            if not self.camera_handler.is_opened():
                print("Warning: Camera not available. Finger tracking disabled.")
                return

            frame_delay = 1.0 / self.config.TARGET_FPS

            while not self.stop_event.is_set():
                try:
                    # Capture frame
                    success, frame = self.camera_handler.read_frame()
                    if not success:
                        print("Failed to grab frame")
                        time.sleep(0.1)
                        continue

                    # Get timestamp
                    timestamp_ms = int(time.time() * 1000)

                    # Detect hands and count fingers
                    total_fingers, _ = self.hand_detector.detect_hands(
                        frame, timestamp_ms
                    )

                    # Update finger count via callback
                    self.on_finger_count_update(total_fingers)

                    # Sleep to maintain target FPS
                    time.sleep(frame_delay)

                except Exception as e:
                    print(f"Error in video processing frame: {e}")
                    time.sleep(0.1)

        except Exception as e:
            print(f"Error initializing video processing: {e}")
