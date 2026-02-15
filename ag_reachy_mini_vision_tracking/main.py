import threading
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


class AgReachyMiniVisionTracking(ReachyMiniApp):
    custom_app_url: str | None = "http://0.0.0.0:8042"
    request_media_backend: str | None = None

    def __init__(self):
        super().__init__()

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
            for cam_index in [0, 1, 2]:
                cap = cv2.VideoCapture(cam_index)
                if cap.isOpened():
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
            # Download model if needed
            model_path = Path.home() / ".mediapipe" / "hand_landmarker.task"
            model_path.parent.mkdir(parents=True, exist_ok=True)

            if not model_path.exists():
                print("Downloading MediaPipe hand landmark model...")
                import urllib.request

                model_url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
                urllib.request.urlretrieve(model_url, model_path)
                print("Model downloaded successfully")

            base_options = python.BaseOptions(model_asset_path=str(model_path))
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.VIDEO,
                num_hands=2,
            )
            self.landmarker = vision.HandLandmarker.create_from_options(options)
            print("MediaPipe Hand Landmarker initialized")

        except Exception as e:
            print(f"Error initializing MediaPipe: {e}")
            cap.release()
            return

        frame_count = 0

        while not stop_event.is_set():
            try:
                ret, frame = cap.read()
                if not ret:
                    print("Failed to grab frame")
                    time.sleep(0.1)
                    continue

                frame_count += 1
                timestamp_ms = int(time.time() * 1000)

                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)

                # Convert BGR to RGB for MediaPipe
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

                # Detect hands
                detection_result = self.landmarker.detect_for_video(
                    mp_image, timestamp_ms
                )

                total_fingers = 0

                # Count fingers from all detected hands
                if detection_result.hand_landmarks:
                    for idx, hand_landmarks in enumerate(
                        detection_result.hand_landmarks
                    ):
                        handedness = detection_result.handedness[idx][0].category_name
                        fingers = self.count_raised_fingers(hand_landmarks, handedness)
                        total_fingers += fingers

                # Update shared state
                with self.finger_count_lock:
                    self.current_finger_count = total_fingers

                time.sleep(0.033)  # ~30 FPS

            except Exception as e:
                print(f"Error in video processing: {e}")
                time.sleep(0.1)

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

        # Start video processing thread
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

            # Get current finger count
            with self.finger_count_lock:
                finger_count = self.current_finger_count

            # Move head based on finger count
            # 0 fingers: look down
            # 5 fingers: look straight
            # 10 fingers: look up
            pitch_deg = (finger_count - 5) * 4.0
            pitch_deg = np.clip(pitch_deg, -20, 20)

            # Add gentle sway
            yaw_deg = 15.0 * np.sin(2.0 * np.pi * 0.1 * t)

            head_pose = create_head_pose(yaw=yaw_deg, pitch=pitch_deg, degrees=True)

            if antennas_enabled:
                # Antennas react to finger count
                amp_deg = min(finger_count * 5.0, 45.0)
                a = amp_deg * np.sin(2.0 * np.pi * 0.5 * t)
                antennas_deg = np.array([a, -a])
            else:
                antennas_deg = np.array([0.0, 0.0])

            if sound_play_requested:
                print("Playing sound...")
                reachy_mini.media.play_sound("wake_up.wav")
                sound_play_requested = False

            antennas_rad = np.deg2rad(antennas_deg)

            reachy_mini.set_target(
                head=head_pose,
                antennas=antennas_rad,
            )

            time.sleep(0.02)

        # Wait for video thread to finish
        video_thread.join(timeout=2.0)


if __name__ == "__main__":
    app = AgReachyMiniVisionTracking()
    try:
        app.wrapped_run()
    except KeyboardInterrupt:
        app.stop()
