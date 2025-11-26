import logging
from logging import Logger

import logging

class LevelBasedFormatter(logging.Formatter):
    def __init__(self):
        super().__init__()
        self.detailed_fmt = logging.Formatter('%(levelname)s - %(filename)s - %(message)s')
        self.simple_fmt = logging.Formatter('%(message)s')
    
    def format(self, record):
        if record.levelno >= logging.WARNING:
            return self.detailed_fmt.format(record)
        else:
            return self.simple_fmt.format(record)

def set_custom_logging_level():
    """silence given packages logging messages"""

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)


def setup_logging(default_level: int = logging.INFO) -> None:
    """Configure root logger with handlers"""

    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        return
    
    root_logger.setLevel(logging.DEBUG)

    # --- console handler ---
    ch = logging.StreamHandler()
    ch.setLevel(default_level)
    ch.setFormatter(LevelBasedFormatter())
    root_logger.addHandler(ch)
    set_custom_logging_level()
    
    root_logger.info(f"Starting new logging session")
 

def get_logger(name: str = __name__) -> Logger:
    """Returns a logger with the specified name"""
    if not logging.getLogger().hasHandlers():
        setup_logging()
    return logging.getLogger(name)
