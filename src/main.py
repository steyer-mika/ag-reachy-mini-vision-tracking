from application import Application
from config.config_loader import get_config
from lib.logger import Logger

logger = Logger(__name__).get()


def main():
    logger.info("Starting Reachy Mini | Vision & Tracking Application")

    config = get_config()

    if not config.MODEL_PATH.exists():
        logger.error(f"Model file not found at {config.MODEL_PATH}")
        logger.error("Please download the hand landmarker model from:")
        logger.error(
            "https://developers.google.com/mediapipe/solutions/vision/hand_landmarker"
        )
        logger.error("Place it in the models/ directory")
        return

    logger.info("Successfully loaded configuration. Starting application...")

    app = Application(config)

    logger.info(
        "Entering main application loop. Press 'q' in the camera window to exit."
    )

    app.run()

    logger.info("Application has exited. Cleaning up resources and shutting down.")


if __name__ == "__main__":
    main()
