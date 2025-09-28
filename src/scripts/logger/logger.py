import logging
from logging import Logger
from pathlib import Path
from datetime import datetime
from scripts.basic_tools import ROOT

_current_log_path: Path | None = None  

def get_logger(name: str = __name__) -> Logger:
    """Returns a logger with the specified name"""
    if not logging.getLogger().hasHandlers():
        setup_logging(setup_logging_path())
    return logging.getLogger(name)

def setup_logging_path() -> Path:
    """Generates the logging path"""
    log_path = ROOT / 'logs'
    log_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f"{timestamp}.log"
    return log_path / log_filename


def setup_logging(log_file_path: Path, default_level: int = logging.INFO) -> None:
    """Configure root logger with handlers"""
    global _current_log_path
    _current_log_path = log_file_path

    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        return  # already configured
    
    root_logger.setLevel(logging.DEBUG)

    # --- file handler ---
    fh = logging.FileHandler(log_file_path, mode='a')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    root_logger.addHandler(fh)

    # --- console handler ---
    ch = logging.StreamHandler()
    ch.setLevel(default_level)
    ch.setFormatter(logging.Formatter('%(message)s'))
    root_logger.addHandler(ch)

    root_logger.info(f"Starting new logging session at {log_file_path}")


def get_log_path() -> Path | None:
    """Return the current log file path (None if logging not set up yet)"""
    return _current_log_path
