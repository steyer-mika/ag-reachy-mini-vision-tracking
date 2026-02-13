from pathlib import Path

from application import Application

MODEL_PATH = Path("./models/hand_landmarker.task")


def main():
    if not MODEL_PATH.exists():
        print(f"Error: Model file not found at {MODEL_PATH}")
        print("Please download the hand landmarker model from MediaPipe")
        return
    
    app = Application(MODEL_PATH)

    app.run()
    
if __name__ == "__main__":
    main()