import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import urllib.request
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List

from ag_reachy_mini_vision_tracking.vision.pid_controller import PIDController

from ..config.config_loader import Config


@dataclass
class DetectedFace:
    x_center: float  # normalized center x (0 = left, 1 = right)
    y_center: float  # normalized center y (0 = top, 1 = bottom)
    width: float  # normalized bounding box width
    height: float  # normalized bounding box height
    score: float  # detection confidence

    @property
    def area(self) -> float:
        return self.width * self.height


@dataclass
class TrackingResult:
    faces: List[DetectedFace] = field(default_factory=list)
    target: Optional[DetectedFace] = None  # primary tracking target
    dx: float = 0.0  # positive = target is to the right
    dy: float = 0.0  # positive = target is below center
    tracking: bool = False
    yaw_correction_deg: float = 0.0  # PID output for yaw correction
    pitch_correction_deg: float = 0.0  # PID output for pitch correction


class FaceTracker:
    def __init__(self, config: Config):
        self.config = config
        self.detector = self._build_detector()

        self.pid_yaw = PIDController(
            kp=config.TRACKING_KP_YAW,
            ki=config.TRACKING_KI_YAW,
            kd=config.TRACKING_KD_YAW,
            output_limit=config.HEAD_YAW_AMPLITUDE,
        )
        self.pid_pitch = PIDController(
            kp=config.TRACKING_KP_PITCH,
            ki=config.TRACKING_KI_PITCH,
            kd=config.TRACKING_KD_PITCH,
            output_limit=config.HEAD_PITCH_MAX,
        )

        self._lost_frames = 0
        self._lost_threshold = config.TRACKING_LOST_THRESHOLD

    def _ensure_model_downloaded(self) -> None:
        model_path = self.config.FACE_MODEL_PATH
        model_path.parent.mkdir(parents=True, exist_ok=True)
        if not model_path.exists():
            print(f"Downloading MediaPipe face detector model to {model_path}…")
            urllib.request.urlretrieve(self.config.FACE_MODEL_URL, model_path)
            print("Face model downloaded successfully.")

    def _build_detector(self):
        self._ensure_model_downloaded()
        base_options = python.BaseOptions(
            model_asset_path=str(self.config.FACE_MODEL_PATH)
        )
        options = vision.FaceDetectorOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            min_detection_confidence=self.config.MIN_DETECTION_CONFIDENCE,
        )
        detector = vision.FaceDetector.create_from_options(options)
        print("MediaPipe FaceDetector initialized.")
        return detector

    def close(self) -> None:
        self.detector.close()

    def _parse_detections(self, result, frame_shape) -> List[DetectedFace]:
        faces: List[DetectedFace] = []
        h, w = frame_shape[:2]
        if not result.detections:
            return faces
        for det in result.detections:
            bb = det.bounding_box
            x_center = (bb.origin_x + bb.width / 2) / w
            y_center = (bb.origin_y + bb.height / 2) / h
            norm_w = bb.width / w
            norm_h = bb.height / h
            score = det.categories[0].score if det.categories else 0.0
            faces.append(DetectedFace(x_center, y_center, norm_w, norm_h, score))
        return faces

    def _select_target(self, faces: List[DetectedFace]) -> Optional[DetectedFace]:
        if not faces:
            return None
        return max(faces, key=lambda f: f.area)

    def update(self, frame: np.ndarray, timestamp_ms: int, dt: float) -> TrackingResult:
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        result = self.detector.detect_for_video(mp_image, timestamp_ms)

        faces = self._parse_detections(result, frame.shape)
        target = self._select_target(faces)

        if target is None:
            self._lost_frames += 1
            if self._lost_frames >= self._lost_threshold:
                self.pid_yaw.reset()
                self.pid_pitch.reset()
            return TrackingResult(faces=faces, tracking=False)

        self._lost_frames = 0
        dx = target.x_center - 0.5
        dy = target.y_center - 0.5

        yaw_correction_deg = -self.pid_yaw.update(dx, dt)
        pitch_correction_deg = self.pid_pitch.update(dy, dt)

        tracking_result = TrackingResult(
            faces=faces, target=target, dx=dx, dy=dy, tracking=True
        )
        tracking_result.yaw_correction_deg = yaw_correction_deg
        tracking_result.pitch_correction_deg = pitch_correction_deg
        return tracking_result
