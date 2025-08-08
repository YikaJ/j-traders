from __future__ import annotations

import logging
from logging import Logger


def setup_logging(level: str = "INFO") -> Logger:
    logger = logging.getLogger("backend-v2")
    if logger.handlers:
        logger.setLevel(level)
        return logger
    logger.setLevel(level)
    handler = logging.StreamHandler()
    fmt = logging.Formatter(
        fmt='%(asctime)s %(levelname)s [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    return logger
