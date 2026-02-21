import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import urllib.request
from typing import Optional, Tuple, Any, List, Dict
import numpy as np

from ..config.config_loader import Config


class HandDetector:
    FINGER_TIPS = [4, 8, 12, 16, 20]
    FINGER_PIPS = [2, 6, 10, 14, 18]

    def __init__(self, config: Config):
        self.config = config
        self.landmarker = None
        self._ensure_model_downloaded()
        self._initialize_landmarker()

    def _ensure_model_downloaded(self) -> None:
        # Download MediaPipe model if not present.
        model_path = self.config.MODEL_PATH
        model_path.parent.mkdir(parents=True, exist_ok=True)

        if not model_path.exists():
            print(f"Downloading MediaPipe hand landmark model to {model_path}...")
            urllib.request.urlretrieve(self.config.HAND_LANDMARKER_MODEL, model_path)
            print("Model downloaded successfully")

    def _initialize_landmarker(self) -> None:
        try:
            base_options = python.BaseOptions(
                model_asset_path=str(self.config.MODEL_PATH)
            )
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.VIDEO,
                num_hands=self.config.MAX_HANDS,
            )
            self.landmarker = vision.HandLandmarker.create_from_options(options)
            print("MediaPipe Hand Landmarker initialized")
        except Exception as e:
            raise RuntimeError(f"Error initializing MediaPipe: {e}")

    def _is_thumb_raised(self, hand_landmarks, handedness: str) -> bool:
        thumb_tip = hand_landmarks[self.FINGER_TIPS[0]]
        thumb_pip = hand_landmarks[self.FINGER_PIPS[0]]

        if handedness == "Right":
            return thumb_tip.x < thumb_pip.x
        else:
            return thumb_tip.x > thumb_pip.x

    def _is_finger_raised(self, hand_landmarks, finger_index: int) -> bool:
        tip = hand_landmarks[self.FINGER_TIPS[finger_index]]
        pip = hand_landmarks[self.FINGER_PIPS[finger_index]]

        return tip.y < pip.y

    def count_raised_fingers(self, hand_landmarks, handedness: str) -> int:
        count = 0

        # Check thumb
        if self._is_thumb_raised(hand_landmarks, handedness):
            count += 1

        # Check other four fingers
        for i in range(1, 5):
            if self._is_finger_raised(hand_landmarks, i):
                count += 1

        return count

    def detect_hands(
        self, frame: np.ndarray | None, timestamp_ms: int
    ) -> Tuple[int, Optional[object], List[Dict[str, Any]]]:
        if self.landmarker is None or frame is None:
            return 0, None, []

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        detection_result = self.landmarker.detect_for_video(mp_image, timestamp_ms)

        total_fingers = 0
        hands_data = []

        if detection_result.hand_landmarks:
            for idx, hand_landmarks in enumerate(detection_result.hand_landmarks):
                handedness = detection_result.handedness[idx][0].category_name
                fingers = self.count_raised_fingers(hand_landmarks, handedness)
                total_fingers += fingers

                # Build individual hand data
                hands_data.append(
                    {
                        "handedness": handedness,
                        "fingers": fingers,
                    }
                )

        return total_fingers, detection_result, hands_data

    def close(self) -> None:
        if self.landmarker:
            self.landmarker.close()
            self.landmarker = None
