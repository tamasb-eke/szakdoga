import logging
from logging import Logger
from pathlib import Path
from datetime import datetime
from scripts.basic_tools import ROOT

_current_log_path: Path | None = None  

def get_logger(name: str = __name__) -> Logger:
    """Returns a logger with the specified name"""
    if not logging.getLogger().hasHandlers():
        setup_logging()
    return logging.getLogger(name)


def setup_logging(default_level: int = logging.INFO) -> None:
    """Configure root logger with handlers"""

    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        return  # already configured
    
    root_logger.setLevel(logging.DEBUG)

    # --- console handler ---
    ch = logging.StreamHandler()
    ch.setLevel(default_level)
    ch.setFormatter(logging.Formatter('%(message)s'))
    root_logger.addHandler(ch)

    root_logger.info(f"Starting new logging session at")
