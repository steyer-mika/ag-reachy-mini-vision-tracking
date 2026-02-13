from pathlib import Path
import cv2
import time

from hand_tracker import HandTracker

WINDOW_HEIGHT = 720
WINDOW_WIDTH = 1280

class Application:
    def __init__(self, model_path: Path):
        self.model_path = model_path

    def run(self):
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, WINDOW_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, WINDOW_HEIGHT)

        print("=" * 60)
        print("HAND-CONTROLLED ROBOT SYSTEM")
        print("=" * 60)
        print("Show 0-10 fingers to trigger robot gestures")
        print("Hold the gesture steady for activation")
        print("Press 'q' to quit")
        print("=" * 60)
        
        frame_count = 0

        try:
            with HandTracker(self.model_path) as tracker:
                while cap.isOpened():
                    success, frame = cap.read()
                    
                    if not success:
                        print("Failed to read from camera")
                        break

                    frame = cv2.flip(frame, 1)

                    timestamp_ms = int(cap.get(cv2.CAP_PROP_POS_MSEC))
                    finger_count, result = tracker.detect(frame, timestamp_ms)
                        
                    # Check if gesture should be triggered
                    current_time = time.time()
                        
                    # Draw visualization
                    annotated_frame = tracker.draw_landmarks(frame, result, finger_count)
                            
                    # Add status info
                    cv2.imshow("Hand-Controlled Robot", annotated_frame)
                        
                    # Exit on 'q'
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break

                    frame_count += 1

        finally:
            cap.release()
            cv2.destroyAllWindows()

            print("Application terminated gracefully.")
            print(f"Total frames processed: {frame_count}")
