import time
import cv2
import asyncio
import threading

from config.config_loader import Config
from tracking.hand_tracker import HandTracker
from lib.logger import Logger
from websocket.websocket_server import WebSocketServer
from robot.robot_controller import RobotController
from tracking.finger_counter import count_raised_fingers


class Application:
    def __init__(self, config: Config):
        self.config = config
        self.logger = Logger(Application.__name__).get()

        # WebSocket server for real-time dashboard updates
        self.ws_server = WebSocketServer(self.config)
        self.ws_thread = None

        # Finger count tracking for robot reaction stability
        # We track the last count and how long it's been stable to avoid
        # reacting to momentary detection glitches
        self.last_finger_count = -1
        self.finger_count_stable_time = 0

        # Exponential Moving Average (EMA) smoothing for UI display
        # This reduces jitter in the displayed count without affecting detection
        self.smoothed_finger_count = 0.0

        # Frame counter for skip-processing optimization
        self.frame_counter = 0

    def start_websocket_server(self) -> None:
        self.ws_thread = threading.Thread(target=self.ws_server.start, daemon=True)
        self.ws_thread.start()
        self.logger.info("WebSocket server thread started")

    def broadcast_finger_count(self, finger_count: int, detection_result) -> None:
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

        # Build per-hand data for detailed dashboard display
        if detection_result.hand_landmarks:
            hands_data = []
            for idx, hand_landmarks in enumerate(detection_result.hand_landmarks):
                handedness = detection_result.handedness[idx][0].category_name
                hand_finger_count = count_raised_fingers(hand_landmarks, handedness)
                hands_data.append(
                    {"handedness": handedness, "fingers": hand_finger_count}
                )
            data["hands"] = hands_data

        # Schedule async broadcast on the WebSocket server's event loop
        # This is thread-safe as we use run_coroutine_threadsafe
        if self.ws_server.loop and self.ws_server.clients:
            asyncio.run_coroutine_threadsafe(
                self.ws_server.broadcast(data), self.ws_server.loop
            )

    def run(self) -> None:
        self.start_websocket_server()

        # Wait for WebSocket server to initialize before proceeding
        time.sleep(self.config.WEBSOCKET_STARTUP_DELAY)

        # Initialize video capture with configured settings
        cap = cv2.VideoCapture(self.config.CAMERA_INDEX)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.CAMERA_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.CAMERA_HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, self.config.TARGET_FPS)
        # Set buffer size to 1 to prevent circular buffer overrun
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        cv2.namedWindow(self.config.WINDOW_HANDLE, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(
            self.config.WINDOW_HANDLE,
            self.config.CAMERA_WIDTH,
            self.config.CAMERA_HEIGHT,
        )

        # FPS tracking for performance monitoring
        frame_duration = 1.0 / self.config.TARGET_FPS
        fps = 0
        fps_counter = 0
        fps_timer = time.perf_counter()

        try:
            with (
                HandTracker(self.config) as tracker,
                RobotController(self.config) as robot,
            ):
                # Perform startup gesture to indicate the system is ready
                robot.startup_gesture()

                # Cache last detection to use during skipped frames
                last_detected_finger_count = 0
                last_result = None

                while cap.isOpened():
                    loop_start = time.perf_counter()
                    success, frame = cap.read()
                    if not success:
                        self.logger.warning("Failed to read frame. Skipping.")
                        continue

                    # Mirror frame for intuitive left/right hand mapping
                    frame = cv2.flip(frame, 1)
                    timestamp_ms = int(cap.get(cv2.CAP_PROP_POS_MSEC))

                    # Frame skipping optimization: only run ML detection every Nth frame
                    # This significantly reduces CPU load while maintaining smooth display
                    if self.frame_counter % self.config.PROCESS_EVERY_N_FRAMES == 0:
                        finger_count, result = tracker.detect(frame, timestamp_ms)
                        last_detected_finger_count = (
                            finger_count if finger_count is not None else 0
                        )
                        last_result = result
                    else:
                        # Reuse last detection result for non-processed frames
                        finger_count = last_detected_finger_count
                        result = last_result

                    # Apply EMA smoothing to reduce jitter in displayed count
                    # Formula: smoothed = alpha * current + (1 - alpha) * previous
                    # Higher alpha = more responsive but more jittery
                    self.smoothed_finger_count = (
                        self.config.SMOOTHING_ALPHA
                        * (finger_count if finger_count is not None else 0)
                        + (1 - self.config.SMOOTHING_ALPHA) * self.smoothed_finger_count
                    )
                    stable_count = round(self.smoothed_finger_count)

                    # Broadcast the smoothed count to connected dashboard clients
                    self.broadcast_finger_count(stable_count, result)

                    # Robot reaction with stability check
                    # Only trigger reaction if count has been stable for REACTION_DELAY seconds
                    # This prevents the robot from reacting to momentary detection glitches
                    current_time = time.perf_counter()
                    if finger_count != self.last_finger_count:
                        # Count changed - reset stability timer
                        self.last_finger_count = finger_count
                        self.finger_count_stable_time = current_time
                    elif (
                        current_time - self.finger_count_stable_time
                        >= self.config.REACTION_DELAY
                    ):
                        # Count has been stable long enough - trigger reaction
                        robot.react_to_finger_count(
                            finger_count if finger_count is not None else 0
                        )
                        # Add cooldown to prevent rapid repeated reactions
                        self.finger_count_stable_time = (
                            current_time + self.config.REACTION_COOLDOWN
                        )

                    # Draw hand landmarks and finger counts on the frame
                    annotated_frame = tracker.draw_landmarks(
                        frame, result, stable_count
                    )

                    # FPS calculation (updated once per second)
                    fps_counter += 1
                    if current_time - fps_timer >= 1.0:
                        fps = fps_counter
                        fps_counter = 0
                        fps_timer = current_time

                    # Draw FPS counter in top-right corner
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

                    # Check for exit key
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        self.logger.info("Exit key pressed. Terminating.")
                        break

                    # Maintain target FPS by sleeping if we finished early
                    elapsed = time.perf_counter() - loop_start
                    sleep_time = frame_duration - elapsed
                    if sleep_time > 0:
                        time.sleep(sleep_time)

                    self.frame_counter += 1

        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")

        finally:
            # Cleanup resources
            cap.release()
            cv2.destroyAllWindows()

            # Give the websocket server time to finish any pending broadcasts
            time.sleep(0.5)
            self.ws_server.stop()

            # Wait for websocket thread to finish
            if self.ws_thread and self.ws_thread.is_alive():
                self.ws_thread.join(timeout=2.0)

            self.logger.info("Application terminated gracefully.")
