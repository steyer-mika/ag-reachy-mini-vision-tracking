import time
import cv2
import asyncio
import threading

from config.config_loader import Config
from tracking.hand_tracker import HandTracker
from lib.logger import Logger
from websocket.websocket_server import WebSocketServer
from robot.robot_controller import RobotController


class Application:
    def __init__(self, config: Config):
        self.config = config
        self.logger = Logger(Application.__name__).get()
        self.ws_server = WebSocketServer(self.config)
        self.ws_thread = None
        self.last_finger_count = -1
        self.finger_count_stable_time = 0
        self.reaction_delay = 0.5  # React after count is stable for 0.5s

    def start_websocket_server(self):
        """Start WebSocket server in a separate thread."""
        self.ws_thread = threading.Thread(target=self.ws_server.start, daemon=True)
        self.ws_thread.start()
        self.logger.info("WebSocket server thread started")

    def broadcast_finger_count(self, finger_count: int, detection_result):
        """Broadcast finger count data to WebSocket clients."""
        data = {
            "type": "finger_count",
            "total": finger_count,
            "timestamp": time.time(),
            "hands_detected": (
                len(detection_result.hand_landmarks)
                if detection_result.hand_landmarks
                else 0
            ),
        }

        # Add per-hand data
        if detection_result.hand_landmarks:
            hands_data = []
            for idx, hand_landmarks in enumerate(detection_result.hand_landmarks):
                from tracking.finger_counter import count_raised_fingers

                handedness = detection_result.handedness[idx][0].category_name
                hand_finger_count = count_raised_fingers(hand_landmarks, handedness)
                hands_data.append(
                    {"handedness": handedness, "fingers": hand_finger_count}
                )
            data["hands"] = hands_data

        # Broadcast using asyncio from the WebSocket server's loop
        if self.ws_server.loop and self.ws_server.clients:
            asyncio.run_coroutine_threadsafe(
                self.ws_server.broadcast(data), self.ws_server.loop
            )

    def run(self):
        """Main application loop."""
        # Start WebSocket server
        self.start_websocket_server()
        time.sleep(1)  # Give the server time to start

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
            with HandTracker(self.config) as tracker, RobotController() as robot:
                # Perform startup gesture
                robot.startup_gesture()

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

                    # Broadcast finger count to WebSocket clients
                    self.broadcast_finger_count(
                        finger_count if finger_count is not None else 0, result
                    )

                    # React to stable finger count
                    current_time = time.perf_counter()
                    if finger_count != self.last_finger_count:
                        self.last_finger_count = finger_count
                        self.finger_count_stable_time = current_time
                    elif (
                        current_time - self.finger_count_stable_time
                        >= self.reaction_delay
                    ):
                        robot.react_to_finger_count(
                            finger_count if finger_count is not None else 0
                        )
                        # Reset timer to avoid continuous updates
                        self.finger_count_stable_time = current_time + 1.0

                    # Draw visualization
                    annotated_frame = tracker.draw_landmarks(
                        frame, result, finger_count
                    )

                    fps_counter += 1

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

            # Stop WebSocket server
            self.ws_server.stop()

            self.logger.info("Application terminated gracefully.")
            self.logger.info(f"Total frames processed: {frame_count}")
