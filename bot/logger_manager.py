"""
Logger manager module for setting up logging configuration.
"""

import logging


class LoggerManager:
    def __init__(self, log_path=None):
        if log_path is None:
            log_path = "bot.log"
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(message)s",
            handlers=[
                logging.FileHandler(log_path),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger()
