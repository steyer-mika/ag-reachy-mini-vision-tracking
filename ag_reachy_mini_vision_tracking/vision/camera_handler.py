import cv2
import numpy as np
from typing import Optional, Tuple

from ..config.config_loader import Config


class CameraHandler:
    def __init__(self, config: Config):
        self.config = config
        self.cap: Optional[cv2.VideoCapture] = None
        self._initialize_camera()

    def _initialize_camera(self) -> None:
        for cam_index in self.config.CAMERA_INDICES:
            cap = cv2.VideoCapture(cam_index)
            if cap.isOpened():
                print(f"Camera opened successfully on index {cam_index}")

                # Set camera properties if needed
                if self.config.CAMERA_WIDTH > 0:
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.CAMERA_WIDTH)
                if self.config.CAMERA_HEIGHT > 0:
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.CAMERA_HEIGHT)

                self.cap = cap
                return
            cap.release()

        raise RuntimeError("Could not open camera on any configured index")

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        if self.cap is None or not self.cap.isOpened():
            return False, None

        ret, frame = self.cap.read()
        if not ret:
            return False, None

        # Flip frame horizontally for mirror effect if configured
        if self.config.CAMERA_FLIP_HORIZONTAL:
            frame = cv2.flip(frame, 1)

        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        return True, frame_rgb

    def is_opened(self) -> bool:
        return self.cap is not None and self.cap.isOpened()

    def release(self) -> None:
        if self.cap:
            self.cap.release()
            self.cap = None
            print("Camera released")
