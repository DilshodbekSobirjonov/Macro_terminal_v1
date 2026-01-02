# services/logger.py

import logging
from logging.handlers import RotatingFileHandler


def setup_logger():
    logger = logging.getLogger("macroterminal")
    logger.setLevel(logging.INFO)

    # ⚠️ чтобы не дублировались логи при рестарте
    if logger.handlers:
        return logger

    # ===== File logger (rotation) =====
    file_handler = RotatingFileHandler(
        "macroterminal.log",
        maxBytes=2 * 1024 * 1024,  # 2 MB
        backupCount=3
    )

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # ===== Console logger (Termux) =====
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger