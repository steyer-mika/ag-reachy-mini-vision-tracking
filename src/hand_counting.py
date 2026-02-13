from pathlib import Path
import cv2
import mediapipe as mp
import numpy as np

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

MODEL_PATH = Path("./models/hand_landmarker.task")
NUM_HANDS = 2


def count_fingers(hand_landmarks, handedness):
    """Count raised fingers on a detected hand."""
    finger_tips = [4, 8, 12, 16, 20]
    finger_pips = [2, 6, 10, 14, 18]

    fingers_up = 0

    # Thumb
    if handedness == "Right":
        if hand_landmarks[finger_tips[0]].x < hand_landmarks[finger_pips[0]].x:
            fingers_up += 1
    else:
        if hand_landmarks[finger_tips[0]].x > hand_landmarks[finger_pips[0]].x:
            fingers_up += 1

    # Other fingers
    for i in range(1, 5):
        if hand_landmarks[finger_tips[i]].y < hand_landmarks[finger_pips[i]].y:
            fingers_up += 1

    return fingers_up


def draw_landmarks_on_frame(frame, detection_result):
    """Draw hand landmarks and finger count on video frame."""
    h, w, _ = frame.shape
    total_fingers = 0

    if detection_result.hand_landmarks:
        for idx, hand_landmarks in enumerate(detection_result.hand_landmarks):
            # Draw landmarks
            for landmark in hand_landmarks:
                x = int(landmark.x * w)
                y = int(landmark.y * h)
                cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)

            # Draw connections
            connections = [
                (0, 1),
                (1, 2),
                (2, 3),
                (3, 4),
                (0, 5),
                (5, 6),
                (6, 7),
                (7, 8),
                (0, 9),
                (9, 10),
                (10, 11),
                (11, 12),
                (0, 13),
                (13, 14),
                (14, 15),
                (15, 16),
                (0, 17),
                (17, 18),
                (18, 19),
                (19, 20),
                (5, 9),
                (9, 13),
                (13, 17),
            ]

            for start_idx, end_idx in connections:
                start = hand_landmarks[start_idx]
                end = hand_landmarks[end_idx]
                start_point = (int(start.x * w), int(start.y * h))
                end_point = (int(end.x * w), int(end.y * h))
                cv2.line(frame, start_point, end_point, (255, 255, 255), 2)

            # Count fingers
            handedness = detection_result.handedness[idx][0].category_name
            finger_count = count_fingers(hand_landmarks, handedness)
            total_fingers += finger_count

            # Draw text
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

    return frame, total_fingers


def main():
    """Run hand tracking on webcam video stream."""
    base_options = python.BaseOptions(model_asset_path=str(MODEL_PATH))
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
        num_hands=NUM_HANDS,
    )

    # Open webcam
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("Hand Tracking - Video Mode")
    print("Press 'q' to quit")
    print("Show 0-10 fingers using both hands")

    frame_count = 0

    with vision.HandLandmarker.create_from_options(options) as landmarker:
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                print("Failed to read from camera")
                break

            # Flip for mirror effect
            frame = cv2.flip(frame, 1)

            # Convert to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Create MediaPipe Image
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

            # Detect hands (need timestamp for VIDEO mode)
            frame_timestamp_ms = int(cap.get(cv2.CAP_PROP_POS_MSEC))
            result = landmarker.detect_for_video(mp_image, frame_timestamp_ms)

            # Write result to json for debugging
            print(f"Frame {frame_count} detection result: {result}")

            # Draw results
            annotated_frame, finger_count = draw_landmarks_on_frame(frame, result)

            print(f"Frame {frame_count}: Detected {finger_count} fingers")

            # Show frame
            cv2.imshow("Hand Tracking - Video", annotated_frame)

            # Exit on 'q'
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            frame_count += 1

    cap.release()
    cv2.destroyAllWindows()
    print(f"\nProcessed {frame_count} frames")


if __name__ == "__main__":
    main()
