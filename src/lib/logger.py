import logging
import sys


class Logger:
    def __init__(self, name: str = "ReachyMini", level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self._get_level(level))

        # Consistent format: timestamp | level | module | message
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Only add handler if one doesn't exist (prevents duplicate logs)
        if not self.logger.handlers:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def _get_level(self, level: str) -> int:
        return {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }.get(level.upper(), logging.INFO)

    def get(self) -> logging.Logger:
        return self.logger
