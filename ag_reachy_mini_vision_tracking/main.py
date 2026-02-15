import threading
import os
import warnings

# Suppress TensorFlow/MediaPipe warnings
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"  # Suppress TensorFlow warnings
warnings.filterwarnings("ignore", category=UserWarning)

from reachy_mini import ReachyMini, ReachyMiniApp
from reachy_mini.utils import create_head_pose
import numpy as np
import time
from pydantic import BaseModel
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from pathlib import Path

from .config.config_loader import get_config


class AgReachyMiniVisionTracking(ReachyMiniApp):
    custom_app_url: str | None = "http://0.0.0.0:8042"
    request_media_backend: str | None = None

    def __init__(self):
        super().__init__()

        # Load config
        self.config = get_config(
            Path(__file__).resolve().parents[0] / "config" / "config.yml"
        )

        # Shared state for finger count
        self.current_finger_count = 0
        self.finger_count_lock = threading.Lock()
        self.landmarker = None

    def is_thumb_raised(self, hand_landmarks, handedness: str) -> bool:
        """Check if thumb is raised based on hand orientation"""
        FINGER_TIPS = [4, 8, 12, 16, 20]
        FINGER_PIPS = [2, 6, 10, 14, 18]

        thumb_tip = hand_landmarks[FINGER_TIPS[0]]
        thumb_pip = hand_landmarks[FINGER_PIPS[0]]

        if handedness == "Right":
            return thumb_tip.x < thumb_pip.x
        else:
            return thumb_tip.x > thumb_pip.x

    def is_finger_raised(self, hand_landmarks, finger_index: int) -> bool:
        """Check if a finger (other than thumb) is raised"""
        FINGER_TIPS = [4, 8, 12, 16, 20]
        FINGER_PIPS = [2, 6, 10, 14, 18]

        tip = hand_landmarks[FINGER_TIPS[finger_index]]
        pip = hand_landmarks[FINGER_PIPS[finger_index]]

        return tip.y < pip.y

    def count_raised_fingers(self, hand_landmarks, handedness: str) -> int:
        """Count number of raised fingers on a hand"""
        count = 0

        # Check thumb
        if self.is_thumb_raised(hand_landmarks, handedness):
            count += 1

        # Check other four fingers
        for i in range(1, 5):
            if self.is_finger_raised(hand_landmarks, i):
                count += 1

        return count

    def process_video_stream(
        self, reachy_mini: ReachyMini, stop_event: threading.Event
    ):
        """Separate thread for video processing with MediaPipe"""
        print("Starting video processing thread...")

        # Try to access camera
        cap = None
        try:
            for cam_index in self.config.CAMERA_INDICES:
                cap = cv2.VideoCapture(cam_index)
                if cap.isOpened():
                    # Set camera properties to reduce buffer issues
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.CAMERA_WIDTH)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.CAMERA_HEIGHT)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to minimum
                    cap.set(cv2.CAP_PROP_FPS, self.config.TARGET_FPS)
                    print(f"Camera opened successfully on index {cam_index}")
                    break
                cap.release()

            if not cap or not cap.isOpened():
                print("Warning: Could not open camera. Finger tracking disabled.")
                return

        except Exception as e:
            print(f"Error opening camera: {e}")
            return

        # Initialize MediaPipe Hand Landmarker
        try:
            model_path = self.config.MODEL_PATH
            model_path.parent.mkdir(parents=True, exist_ok=True)

            if not model_path.exists():
                print("Downloading MediaPipe hand landmark model...")
                import urllib.request

                urllib.request.urlretrieve(self.config.MODEL_URL, model_path)
                print("Model downloaded successfully")

            base_options = python.BaseOptions(model_asset_path=str(model_path))
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.VIDEO,
                num_hands=self.config.MAX_HANDS,
                min_hand_detection_confidence=self.config.MIN_DETECTION_CONFIDENCE,
                min_hand_presence_confidence=self.config.MIN_TRACKING_CONFIDENCE,
                min_tracking_confidence=self.config.MIN_TRACKING_CONFIDENCE,
            )
            self.landmarker = vision.HandLandmarker.create_from_options(options)
            print("MediaPipe Hand Landmarker initialized")

        except Exception as e:
            print(f"Error initializing MediaPipe: {e}")
            cap.release()
            return

        while not stop_event.is_set():
            # Grab latest frame and discard buffered frames to prevent lag
            cap.grab()  # Discard buffered frames
            ret, frame = cap.retrieve()

            if not ret:
                time.sleep(1 / self.config.TARGET_FPS)
                continue

            # Flip if configured
            if self.config.CAMERA_FLIP_HORIZONTAL:
                frame = cv2.flip(frame, 1)

            # Convert to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

            # Detect hands
            timestamp_ms = int(time.time() * 1000)
            detection_result = self.landmarker.detect_for_video(mp_image, timestamp_ms)

            total_fingers = 0
            if detection_result.hand_landmarks:
                for idx, hand_landmarks in enumerate(detection_result.hand_landmarks):
                    handedness = detection_result.handedness[idx][0].category_name
                    fingers = self.count_raised_fingers(hand_landmarks, handedness)
                    total_fingers += fingers

            with self.finger_count_lock:
                self.current_finger_count = total_fingers

            time.sleep(1 / self.config.TARGET_FPS)

        # Cleanup
        if self.landmarker:
            self.landmarker.close()
        if cap:
            cap.release()
        print("Video processing thread stopped")

    def run(self, reachy_mini: ReachyMini, stop_event: threading.Event):
        t0 = time.time()
        antennas_enabled = True
        sound_play_requested = False

        # Start video thread
        video_thread = threading.Thread(
            target=self.process_video_stream,
            args=(reachy_mini, stop_event),
            daemon=True,
        )
        video_thread.start()

        # API endpoints
        class AntennaState(BaseModel):
            enabled: bool

        if self.settings_app:

            @self.settings_app.post("/antennas")
            def update_antennas_state(state: AntennaState):
                nonlocal antennas_enabled
                antennas_enabled = state.enabled
                return {"antennas_enabled": antennas_enabled}

            @self.settings_app.post("/play_sound")
            def request_sound_play():
                nonlocal sound_play_requested
                sound_play_requested = True

            @self.settings_app.get("/finger_count")
            def get_finger_count():
                """Return current finger count"""
                with self.finger_count_lock:
                    return {"finger_count": self.current_finger_count}

        # Main control loop
        while not stop_event.is_set():
            t = time.time() - t0
            with self.finger_count_lock:
                finger_count = self.current_finger_count

            # Head pitch based on finger count
            pitch_deg = np.clip(
                (finger_count - 5) * self.config.HEAD_PITCH_SCALE,
                self.config.HEAD_PITCH_MIN,
                self.config.HEAD_PITCH_MAX,
            )

            # Yaw sway
            yaw_deg = self.config.HEAD_YAW_AMPLITUDE * np.sin(
                2.0 * np.pi * self.config.HEAD_YAW_FREQUENCY * t
            )

            head_pose = create_head_pose(yaw=yaw_deg, pitch=pitch_deg, degrees=True)

            # Antennas
            if antennas_enabled:
                amp_deg = min(
                    finger_count * self.config.ANTENNA_SCALE,
                    self.config.ANTENNA_MAX_AMPLITUDE,
                )
                a = amp_deg * np.sin(2.0 * np.pi * self.config.ANTENNA_FREQUENCY * t)
                antennas_deg = np.array([a, -a])
            else:
                antennas_deg = np.array([0.0, 0.0])

            if sound_play_requested:
                print("Playing sound...")
                reachy_mini.media.play_sound("wake_up.wav")
                sound_play_requested = False

            antennas_rad = np.deg2rad(antennas_deg)

            reachy_mini.set_target(head=head_pose, antennas=antennas_rad)

            time.sleep(self.config.CONTROL_LOOP_RATE)

        video_thread.join(timeout=2.0)


if __name__ == "__main__":
    app = AgReachyMiniVisionTracking()
    try:
        app.wrapped_run()
    except KeyboardInterrupt:
        app.stop()
