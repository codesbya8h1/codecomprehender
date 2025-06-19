"""Simple logging for Code Comprehender."""

import logging
import sys

# Simple global logger setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)

# Reduce noise from external libraries
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger("code_comprehender")


def get_logger(name: str = "code_comprehender") -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


def set_log_level(level: str):
    """Set the global log level."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.getLogger().setLevel(numeric_level)


def log_progress(message: str, current: int = None, total: int = None):
    """Log progress message."""
    if current is not None and total is not None:
        logger.info(f"[{current}/{total}] {message}")


def log_success(message: str):
    """Log success message."""
    logger.info(f"SUCCESS: {message}")


def log_warning(message: str):
    """Log warning message."""
    logger.warning(f"WARNING: {message}")


def log_error(message: str):
    """Log error message."""
    logger.error(f"ERROR: {message}")
