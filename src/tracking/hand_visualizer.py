import cv2
import numpy as np
from typing import Optional

from tracking.hand_constants import (
    HAND_CONNECTIONS,
    LANDMARK_COLOR,
    CONNECTION_COLOR,
    TEXT_COLOR,
    TOTAL_TEXT_COLOR,
    LANDMARK_RADIUS,
    CONNECTION_THICKNESS,
    TEXT_THICKNESS,
)
from tracking.finger_counter import count_raised_fingers


def draw_hand_landmarks(frame: np.ndarray, hand_landmarks) -> None:
    h, w, _ = frame.shape

    # Draw landmark points (joint markers)
    for landmark in hand_landmarks:
        # Convert normalized coordinates (0-1) to pixel coordinates
        x = int(landmark.x * w)
        y = int(landmark.y * h)
        cv2.circle(frame, (x, y), LANDMARK_RADIUS, LANDMARK_COLOR, -1)

    # Draw skeleton connections (lines between joints)
    for start_idx, end_idx in HAND_CONNECTIONS:
        start = hand_landmarks[start_idx]
        end = hand_landmarks[end_idx]
        start_point = (int(start.x * w), int(start.y * h))
        end_point = (int(end.x * w), int(end.y * h))
        cv2.line(frame, start_point, end_point, CONNECTION_COLOR, CONNECTION_THICKNESS)


def draw_finger_count_label(
    frame: np.ndarray, hand_landmarks, handedness: str, finger_count: int
) -> None:
    h, w, _ = frame.shape
    wrist = hand_landmarks[0]  # Wrist is always landmark 0

    # Position text slightly above and to the left of wrist
    text_pos = (int(wrist.x * w) - 50, int(wrist.y * h) - 30)
    text = f"{handedness}: {finger_count}"

    cv2.putText(
        frame,
        text,
        text_pos,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        TEXT_COLOR,
        TEXT_THICKNESS,
    )


def draw_total_count(frame: np.ndarray, total_fingers: Optional[int]) -> None:
    count = total_fingers if total_fingers is not None else 0
    cv2.putText(
        frame,
        f"Total: {count}",
        (10, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.2,
        TOTAL_TEXT_COLOR,
        3,
    )


def visualize_detection(
    frame: np.ndarray, detection_result, total_fingers: Optional[int] = 0
) -> np.ndarray:
    # Draw visualization for each detected hand
    if detection_result.hand_landmarks:
        for idx, hand_landmarks in enumerate(detection_result.hand_landmarks):
            handedness = detection_result.handedness[idx][0].category_name
            finger_count = count_raised_fingers(hand_landmarks, handedness)

            draw_hand_landmarks(frame, hand_landmarks)
            draw_finger_count_label(frame, hand_landmarks, handedness, finger_count)

    # Draw aggregate total count
    draw_total_count(frame, total_fingers)

    return frame
