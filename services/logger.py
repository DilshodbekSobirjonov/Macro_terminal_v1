# services/logger.py

import logging
from logging.handlers import RotatingFileHandler

def setup_logger():
    logger = logging.getLogger("macroterminal")
    logger.setLevel(logging.INFO)

    handler = RotatingFileHandler(
        "macroterminal.log",
        maxBytes=2 * 1024 * 1024,  # 2 MB
        backupCount=3
    )
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger