import cv2

from config.config_loader import Config
from hand_tracker import HandTracker
from lib.logger import Logger


class Application:
    def __init__(self, config: Config):
        self.config = config
        self.logger = Logger(Application.__name__).get()

    def run(self):
        cap = cv2.VideoCapture(self.config.CAMERA_INDEX)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.CAMERA_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.CAMERA_HEIGHT)

        cv2.namedWindow(self.config.WINDOW_HANDLE, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(
            self.config.WINDOW_HANDLE,
            self.config.CAMERA_WIDTH,
            self.config.CAMERA_HEIGHT,
        )

        frame_count = 0

        try:
            with HandTracker(self.config) as tracker:
                while cap.isOpened():
                    success, frame = cap.read()

                    if not success:
                        self.logger.warning(
                            "Failed to read frame from camera. Skipping to next frame..."
                        )
                        continue

                    # Skip frames for performance
                    if frame_count % self.config.CAMERA_FRAME_SKIP != 0:
                        frame_count += 1
                        continue

                    # Flip the frame, because MediaPipe's hand tracking is designed for selfie mode
                    frame = cv2.flip(frame, 1)

                    timestamp_ms = int(cap.get(cv2.CAP_PROP_POS_MSEC))
                    finger_count, result = tracker.detect(frame, timestamp_ms)

                    # Draw visualization
                    annotated_frame = tracker.draw_landmarks(
                        frame, result, finger_count
                    )

                    # Add status info
                    cv2.imshow(self.config.WINDOW_HANDLE, annotated_frame)

                    # Exit on 'q' (Note: Only works if the camera window is focused - not the terminal)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        self.logger.info(
                            "Exit key 'q' pressed. Exiting application loop."
                        )
                        break

                    frame_count += 1

        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")

        finally:
            cap.release()
            cv2.destroyAllWindows()

            self.logger.info("Application terminated gracefully.")
            self.logger.info(f"Total frames processed: {frame_count}")
