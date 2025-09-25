import logging
from logging import Logger
from pathlib import Path
from datetime import datetime
from scripts.basic_tools import ROOT

def get_logger(name:str = __name__) -> Logger:
    """Returns a logger with the specified name"""

    if not logging.getLogger().hasHandlers():
        setup_logging()
    
    return logging.getLogger(name)

def setup_logging_path() -> Path:
    """Generates the logging path"""
    log_path = ROOT / 'logs'
    timestamp = datetime.now().strftime('%Y%m%d %H%M%S')
    log_filename = f"{timestamp}.log"

    return log_path / log_filename

def setup_logging(log_file_path:Path, default_level:int = logging.INFO) -> None:
    """Configure root logger with handlers"""

    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        return #already configured
    
    #--- file handler ---
    fh = logging.FileHandler(log_file_path, mode='a')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))

    root_logger.addHandler(fh)

    #--- Console handler ---
    ch = logging.StreamHandler()
    ch.setLevel(default_level)
    ch.setFormatter(logging.Formatter('%(message)s'))
    root_logger.addHandler(ch)

    root_logger.debug(f"Starting new logging session at {log_file_path}")

setup_logging(log_file_path=setup_logging_path())