from application import Application
from config.config_loader import get_config

def main():
    config = get_config()

    if not config.MODEL_PATH.exists():
        print(f"Error: Model file not found at {config.MODEL_PATH}")
        print("Please download the hand landmarker model from MediaPipe")
        return

    app = Application(config)

    app.run()
    
if __name__ == "__main__":
    main()