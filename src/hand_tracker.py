from pathlib import Path
from typing import Tuple, Optional
import cv2
import mediapipe as mp
import numpy as np

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class HandTracker:
    def __init__(self, model_path: Path, num_hands: int = 2):
        self.model_path = model_path
        self.num_hands = num_hands
        self.landmarker = None
        
    def __enter__(self):
        base_options = python.BaseOptions(model_asset_path=str(self.model_path))
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=self.num_hands,
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.landmarker:
            self.landmarker.close()
    
    @staticmethod
    def count_fingers(hand_landmarks, handedness: str) -> int:
        finger_tips = [4, 8, 12, 16, 20]
        finger_pips = [2, 6, 10, 14, 18]
        fingers_up = 0

        # Thumb (different logic based on hand orientation)
        if handedness == "Right":
            if hand_landmarks[finger_tips[0]].x < hand_landmarks[finger_pips[0]].x:
                fingers_up += 1
        else:
            if hand_landmarks[finger_tips[0]].x > hand_landmarks[finger_pips[0]].x:
                fingers_up += 1

        # Other fingers (tip above pip joint = raised)
        for i in range(1, 5):
            if hand_landmarks[finger_tips[i]].y < hand_landmarks[finger_pips[i]].y:
                fingers_up += 1

        return fingers_up
    
    def detect(self, frame: np.ndarray, timestamp_ms: int) -> Tuple[Optional[int], object]:
        if self.landmarker is None:
            raise RuntimeError("HandTracker must be used within a context manager")

        # Convert to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Create MediaPipe Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        # Detect hands
        result = self.landmarker.detect_for_video(mp_image, timestamp_ms)
        
        # Count total fingers
        total_fingers = 0
        if result.hand_landmarks:
            for idx, hand_landmarks in enumerate(result.hand_landmarks):
                handedness = result.handedness[idx][0].category_name
                finger_count = self.count_fingers(hand_landmarks, handedness)
                total_fingers += finger_count
        
        return total_fingers, result
    
    @staticmethod
    def draw_landmarks(frame: np.ndarray, detection_result, total_fingers: int | None = 0) -> np.ndarray:
        h, w, _ = frame.shape

        if detection_result.hand_landmarks:
            for idx, hand_landmarks in enumerate(detection_result.hand_landmarks):
                # Draw landmarks
                for landmark in hand_landmarks:
                    x = int(landmark.x * w)
                    y = int(landmark.y * h)
                    cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)

                # Draw connections
                connections = [
                    (0, 1), (1, 2), (2, 3), (3, 4),  # Thumb
                    (0, 5), (5, 6), (6, 7), (7, 8),  # Index
                    (0, 9), (9, 10), (10, 11), (11, 12),  # Middle
                    (0, 13), (13, 14), (14, 15), (15, 16),  # Ring
                    (0, 17), (17, 18), (18, 19), (19, 20),  # Pinky
                    (5, 9), (9, 13), (13, 17),  # Palm
                ]

                for start_idx, end_idx in connections:
                    start = hand_landmarks[start_idx]
                    end = hand_landmarks[end_idx]
                    start_point = (int(start.x * w), int(start.y * h))
                    end_point = (int(end.x * w), int(end.y * h))
                    cv2.line(frame, start_point, end_point, (255, 255, 255), 2)

                # Count and display per-hand fingers
                handedness = detection_result.handedness[idx][0].category_name
                finger_count = HandTracker.count_fingers(hand_landmarks, handedness)

                # Draw text near wrist
                wrist = hand_landmarks[0]
                text_pos = (int(wrist.x * w) - 50, int(wrist.y * h) - 30)
                cv2.putText(
                    frame,
                    f"{handedness}: {finger_count}",
                    text_pos,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )

        # Total count
        cv2.putText(
            frame,
            f"Total: {total_fingers}",
            (10, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (255, 0, 0),
            3,
        )

        return frame