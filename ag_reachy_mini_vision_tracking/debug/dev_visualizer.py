import time
import cv2
import numpy as np
from typing import Optional

from ..vision.face_tracker import TrackingResult
from ..vision.hand_detector import HandDetector

# ── Visual style constants ────────────────────────────────────────────────
LANDMARK_COLOR = (0, 255, 0)  # green dots
CONNECTION_COLOR = (255, 255, 0)  # yellow skeleton lines
TEXT_COLOR = (255, 255, 255)  # white per-hand label
TOTAL_TEXT_COLOR = (0, 255, 255)  # cyan total-fingers label
FACE_BOX_COLOR = (255, 80, 80)  # coral - non-target faces
FACE_TARGET_COLOR = (0, 200, 255)  # orange - primary tracking target
FPS_COLOR = (0, 255, 0)  # green FPS counter

LANDMARK_RADIUS = 4
CONNECTION_THICKNESS = 2
TEXT_THICKNESS = 2

HAND_CONNECTIONS = [
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),  # Thumb
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),  # Index
    (0, 9),
    (9, 10),
    (10, 11),
    (11, 12),  # Middle
    (0, 13),
    (13, 14),
    (14, 15),
    (15, 16),  # Ring
    (0, 17),
    (17, 18),
    (18, 19),
    (19, 20),  # Pinky
    (5, 9),
    (9, 13),
    (13, 17),  # Palm
]


def _draw_hand_landmarks(frame: np.ndarray, hand_landmarks) -> None:
    h, w = frame.shape[:2]
    for lm in hand_landmarks:
        cv2.circle(
            frame, (int(lm.x * w), int(lm.y * h)), LANDMARK_RADIUS, LANDMARK_COLOR, -1
        )
    for s_idx, e_idx in HAND_CONNECTIONS:
        s, e = hand_landmarks[s_idx], hand_landmarks[e_idx]
        cv2.line(
            frame,
            (int(s.x * w), int(s.y * h)),
            (int(e.x * w), int(e.y * h)),
            CONNECTION_COLOR,
            CONNECTION_THICKNESS,
        )


def _draw_finger_count_label(
    frame: np.ndarray, hand_landmarks, handedness: str, finger_count: int
) -> None:
    h, w = frame.shape[:2]
    wrist = hand_landmarks[0]
    cv2.putText(
        frame,
        f"{handedness}: {finger_count}",
        (int(wrist.x * w) - 50, int(wrist.y * h) - 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        TEXT_COLOR,
        TEXT_THICKNESS,
    )


def _draw_total_count(frame: np.ndarray, total: int) -> None:
    cv2.putText(
        frame,
        f"Total fingers: {total}",
        (10, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.2,
        TOTAL_TEXT_COLOR,
        3,
    )


def _draw_fps(frame: np.ndarray, fps: int, frame_width: int) -> None:
    text = f"FPS: {fps}"
    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
    cv2.putText(
        frame,
        text,
        (frame_width - text_size[0] - 10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        FPS_COLOR,
        2,
        cv2.LINE_AA,
    )


def _draw_faces(frame: np.ndarray, tracking_result: Optional[TrackingResult]) -> None:
    if tracking_result is None or not tracking_result.faces:
        return

    h, w = frame.shape[:2]

    for face in tracking_result.faces:
        is_target = (
            tracking_result.target is not None and face is tracking_result.target
        )
        color = FACE_TARGET_COLOR if is_target else FACE_BOX_COLOR
        thickness = 3 if is_target else 1

        bx = int((face.x_center - face.width / 2) * w)
        by = int((face.y_center - face.height / 2) * h)
        bw = int(face.width * w)
        bh = int(face.height * h)

        cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), color, thickness)

        label = "TARGET" if is_target else f"{face.score:.0%}"
        cv2.putText(
            frame,
            label,
            (bx, by - 6),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            1,
            cv2.LINE_AA,
        )

    # Cross-hair at the frame centre so offset is visually obvious
    cx, cy = w // 2, h // 2
    cv2.drawMarker(
        frame, (cx, cy), (200, 200, 200), cv2.MARKER_CROSS, markerSize=30, thickness=1
    )


def _draw_tracking_status(
    frame: np.ndarray, tracking_result: Optional[TrackingResult]
) -> None:
    if tracking_result is None:
        status = "No tracking data"
        color = (128, 128, 128)
    elif tracking_result.tracking:
        n = len(tracking_result.faces)
        status = f"Tracking  |  {n} face{'s' if n != 1 else ''} detected"
        color = FACE_TARGET_COLOR
    else:
        status = "Searching…"
        color = (200, 200, 0)

    cv2.putText(frame, status, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)


def _count_fingers(hand_landmarks, handedness: str) -> int:
    tips = HandDetector.FINGER_TIPS
    pips = HandDetector.FINGER_PIPS
    count = 0
    tip, pip = hand_landmarks[tips[0]], hand_landmarks[pips[0]]
    count += int(tip.x < pip.x) if handedness == "Right" else int(tip.x > pip.x)
    for i in range(1, 5):
        count += int(hand_landmarks[tips[i]].y < hand_landmarks[pips[i]].y)
    return count


class DevVisualizer:
    WINDOW = "Reachy Mini | Dev View"

    def __init__(self, config):
        self.config = config
        self._fps: int = 0
        self._fps_counter: int = 0
        self._fps_timer: float = time.perf_counter()  # always a float, never None
        self._opened: bool = False

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def open(self) -> None:
        if self._opened:
            return
        self._fps_timer = time.perf_counter()
        cv2.namedWindow(self.WINDOW, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(
            self.WINDOW, self.config.CAMERA_WIDTH, self.config.CAMERA_HEIGHT
        )
        self._opened = True

    def close(self) -> None:
        if self._opened:
            cv2.destroyWindow(self.WINDOW)
            self._opened = False

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *_):
        self.close()

    # ── Per-frame API ─────────────────────────────────────────────────────

    def annotate(
        self,
        frame: np.ndarray,
        hand_result,  # MediaPipe HandLandmarkerResult | None
        tracking_result: Optional[TrackingResult],
        total_fingers: int,
    ) -> np.ndarray:
        out = frame.copy()

        # Hand landmarks + per-hand finger count labels
        if hand_result is not None and hand_result.hand_landmarks:
            for idx, hand_landmarks in enumerate(hand_result.hand_landmarks):
                handedness = hand_result.handedness[idx][0].category_name
                finger_count = _count_fingers(hand_landmarks, handedness)
                _draw_hand_landmarks(out, hand_landmarks)
                _draw_finger_count_label(out, hand_landmarks, handedness, finger_count)

        _draw_total_count(out, total_fingers)
        _draw_faces(out, tracking_result)
        _draw_tracking_status(out, tracking_result)
        self._update_fps(out)

        return out

    def show(self, frame: np.ndarray) -> bool:
        if not self._opened:
            return False
        bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imshow(self.WINDOW, bgr)
        return (cv2.waitKey(1) & 0xFF) == ord("q")

    def _update_fps(self, frame: np.ndarray) -> None:
        self._fps_counter += 1
        now: float = time.perf_counter()
        if now - self._fps_timer >= 1.0:
            self._fps = self._fps_counter
            self._fps_counter = 0
            self._fps_timer = now
        _draw_fps(frame, self._fps, self.config.CAMERA_WIDTH)
