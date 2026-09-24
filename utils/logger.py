"""
utils/logger.py
----------------
Central logging configuration.

Logs go to:
- the console (stdout) — so you see activity while running locally / in
  your deployment platform's log viewer
- a rotating file at logs/bot.log — so you have a persistent record even
  after the console is closed. The file auto-rotates so it never grows
  unbounded.
"""

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging(log_level: str = None) -> None:
    level_name = (log_level or os.getenv("LOG_LEVEL", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)

    os.makedirs("logs", exist_ok=True)

    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    formatter = logging.Formatter(log_format)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid duplicate handlers if setup_logging() is ever called twice
    if root_logger.handlers:
        return

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        "logs/bot.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # The underlying HTTP library used by python-telegram-bot is very chatty
    # at INFO level (logs every API call). Quiet it down to WARNING.
    logging.getLogger("httpx").setLevel(logging.WARNING)
