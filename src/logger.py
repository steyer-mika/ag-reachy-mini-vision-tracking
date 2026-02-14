import logging
import sys


class Logger:
    def __init__(self, name: str = "ReachyMini", level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self._get_level(level))

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def _get_level(self, level: str):
        return {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }.get(level.upper(), logging.INFO)

    def get(self):
        return self.logger
