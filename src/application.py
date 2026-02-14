import time
import cv2

from config.config_loader import Config
from tracking.hand_tracker import HandTracker
from lib.logger import Logger


class Application:
    def __init__(self, config: Config):
        self.config = config
        self.logger = Logger(Application.__name__).get()

    def run(self):
        cap = cv2.VideoCapture(self.config.CAMERA_INDEX)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.CAMERA_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.CAMERA_HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, self.config.TARGET_FPS)

        cv2.namedWindow(self.config.WINDOW_HANDLE, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(
            self.config.WINDOW_HANDLE,
            self.config.CAMERA_WIDTH,
            self.config.CAMERA_HEIGHT,
        )

        frame_count = 0
        frame_duration = 1.0 / self.config.TARGET_FPS

        fps = 0
        fps_counter = 0
        fps_timer = time.perf_counter()

        try:
            with HandTracker(self.config) as tracker:
                while cap.isOpened():
                    loop_start = time.perf_counter()

                    success, frame = cap.read()

                    if not success:
                        self.logger.warning(
                            "Failed to read frame from camera. Skipping to next frame..."
                        )
                        continue

                    # Flip the frame, because MediaPipe's hand tracking is designed for selfie mode
                    frame = cv2.flip(frame, 1)

                    timestamp_ms = int(cap.get(cv2.CAP_PROP_POS_MSEC))
                    finger_count, result = tracker.detect(frame, timestamp_ms)

                    # Draw visualization
                    annotated_frame = tracker.draw_landmarks(
                        frame, result, finger_count
                    )

                    fps_counter += 1
                    current_time = time.perf_counter()

                    if current_time - fps_timer >= 1.0:
                        fps = fps_counter
                        fps_counter = 0
                        fps_timer = current_time

                    text = f"FPS: {fps}"
                    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
                    cv2.putText(
                        annotated_frame,
                        text,
                        (self.config.CAMERA_WIDTH - text_size[0] - 10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        2,
                        cv2.LINE_AA,
                    )

                    cv2.imshow(self.config.WINDOW_HANDLE, annotated_frame)

                    # Exit on 'q'
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        self.logger.info(
                            "Exit key 'q' pressed. Exiting application loop."
                        )
                        break

                    elapsed = time.perf_counter() - loop_start
                    sleep_time = frame_duration - elapsed
                    if sleep_time > 0:
                        time.sleep(sleep_time)

                    frame_count += 1

        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")

        finally:
            cap.release()
            cv2.destroyAllWindows()

            self.logger.info("Application terminated gracefully.")
            self.logger.info(f"Total frames processed: {frame_count}")
