import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime


class CustomFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[94m',    # Light Blue
        'INFO': '\033[92m',     # Light Green
        'WARNING': '\033[93m',  # Light Yellow
        'ERROR': '\033[91m',    # Light Red
        'CRITICAL': '\033[95m', # Light Magenta
    } 
    RESET = '\033[0m'

    def format(self, record):
        record.message = record.getMessage()
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S.%f")[:-3]
        name = record.name
        color = self.COLORS.get(record.levelname, self.RESET)
        return f"{timestamp} | {color}{record.levelname:<7}{self.RESET} | {name} - {record.message}"


def setup_logger(name: str, log_file: str = None, log_level: str = None) -> logging.Logger:
    log_level = log_level or os.environ.get('LOGLEVEL', 'INFO').upper()
    numeric_level = getattr(logging, log_level, None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')

    logger = logging.getLogger(name)
    logger.setLevel(numeric_level)

    # Clear any existing handlers
    logger.handlers.clear()

    # Prevent propagation to the root logger
    logger.propagate = False

    # Create a formatter
    formatter = CustomFormatter()

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(numeric_level)
    logger.addHandler(console_handler)

    # Create file handler if log_file is specified
    if log_file:
        file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(numeric_level)
        logger.addHandler(file_handler)

    logger.debug(f"Logger {name} initialized with level {log_level}")

    return logger

def get_log_file_path(run_dir: str, filename: str = "my_engineer.log") -> str:
    return os.path.join(run_dir, filename)
