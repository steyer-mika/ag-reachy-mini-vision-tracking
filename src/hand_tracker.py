from pathlib import Path
import cv2
import mediapipe as mp
import numpy as np

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

MODEL_PATH = Path("./models/hand_landmarker.task")
IMAGE_PATH = Path("./image.jpg")

base_options = python.BaseOptions(model_asset_path=str(MODEL_PATH))

options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.IMAGE,
    num_hands=2,
)


def draw_landmarks_on_image(rgb_image, detection_result):
    annotated_image = rgb_image.copy()

    for hand_landmarks in detection_result.hand_landmarks:
        h, w, _ = annotated_image.shape

        for landmark in hand_landmarks:
            x = int(landmark.x * w)
            y = int(landmark.y * h)

            cv2.circle(annotated_image, (x, y), 5, (0, 255, 0), -1)

    return annotated_image


with vision.HandLandmarker.create_from_options(options) as landmarker:
    mp_image = mp.Image.create_from_file(str(IMAGE_PATH))

    result = landmarker.detect(mp_image)

    rgb_image = mp_image.numpy_view()

    annotated_image = draw_landmarks_on_image(rgb_image, result)

    annotated_image = cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR)

    cv2.namedWindow("Hand Landmarks", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Hand Landmarks", 800, 600)  # width, height
    cv2.imshow("Hand Landmarks", annotated_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
