# utils/logger.py
# -----------------------------------------------
# Sets up logging for the entire project.
# Every other file will import get_logger() from here
# and use it to record what's happening.
# -----------------------------------------------

import logging
import os
from logging.handlers import RotatingFileHandler


def get_logger(name: str) -> logging.Logger:
    """
    Call this from any file like:
        from utils.logger import get_logger
        logger = get_logger(__name__)
    Then use:
        logger.info("something happened")
        logger.error("something broke")
        logger.debug("detailed info")
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if this function is called twice
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # How each log line will look:
    # 2024-01-15 14:32:01 | INFO     | scrapers.ebay_scraper | Found 45 results
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # --- Console handler: shows INFO and above in terminal ---
    console_handler = logging.StreamHandler()
    console_handler.stream = open(
    __import__('sys').stdout.fileno(),
    mode='w',
    encoding='utf-8',
    buffering=1
    )
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # --- File handler: saves DEBUG and above to a log file ---
    os.makedirs("logs", exist_ok=True)  # creates logs/ folder if it doesn't exist
    file_handler = RotatingFileHandler(
        "logs/scraper.log",
        maxBytes=10_000_000,   # 10MB max per file
        backupCount=3           # keep 3 old log files before deleting
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger