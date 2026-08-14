import logging
import sys

from app.config import get_settings


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("codevoyager")
    logger.setLevel(getattr(logging, get_settings().log_level, logging.INFO))
    logger.propagate = False

    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    handler.setFormatter(
        formatter
    )

    logger.addHandler(handler)

    return logger


logger = setup_logger()
