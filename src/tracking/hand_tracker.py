from typing import Tuple, Optional
import cv2
import mediapipe as mp
import numpy as np

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from config.config_loader import Config
from tracking.finger_counter import count_raised_fingers
from tracking.hand_visualizer import visualize_detection


class HandTracker:
    def __init__(self, config: Config):
        self.config = config
        self.landmarker = None

    def __enter__(self):
        base_options = python.BaseOptions(model_asset_path=str(self.config.MODEL_PATH))
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=2,  # TODO: Make multi-hand support configurable
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)
        return self

    def __exit__(self, _exc_type, _exc_val, _exc_tb):
        if self.landmarker:
            self.landmarker.close()

    def _prepare_frame(self, frame: np.ndarray) -> mp.Image:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

    def _count_total_fingers(self, detection_result) -> int:
        total = 0

        if detection_result.hand_landmarks:
            for idx, hand_landmarks in enumerate(detection_result.hand_landmarks):
                handedness = detection_result.handedness[idx][0].category_name
                total += count_raised_fingers(hand_landmarks, handedness)

        return total

    def detect(
        self, frame: np.ndarray, timestamp_ms: int
    ) -> Tuple[Optional[int], object]:
        if self.landmarker is None:
            raise RuntimeError("HandTracker must be used within a context manager")

        mp_image = self._prepare_frame(frame)
        detection_result = self.landmarker.detect_for_video(mp_image, timestamp_ms)
        total_fingers = self._count_total_fingers(detection_result)

        return total_fingers, detection_result

    @staticmethod
    def draw_landmarks(
        frame: np.ndarray, detection_result, total_fingers: Optional[int] = 0
    ) -> np.ndarray:
        return visualize_detection(frame, detection_result, total_fingers)
