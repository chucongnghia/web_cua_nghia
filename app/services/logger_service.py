import logging
import os
from datetime import datetime
from flask import current_app

_logger_instance = None


def get_activity_logger(log_file_path: str = None) -> logging.Logger:
    global _logger_instance
    if _logger_instance is not None and not log_file_path:
        return _logger_instance

    if not log_file_path:
        try:
            log_file_path = current_app.config.get("LOG_FILE", "app.log")
        except RuntimeError:
            log_file_path = "app.log"

    os.makedirs(os.path.dirname(os.path.abspath(log_file_path)), exist_ok=True)

    logger = logging.getLogger("StudyDocsActivity")
    logger.setLevel(logging.INFO)

    # Avoid adding multiple handlers if already initialized
    if not logger.handlers:
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [USER: %(username)s] %(action)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    _logger_instance = logger
    return logger


def log_activity(
    action: str, username: str = "anonymous", details: str = "", level: str = "INFO"
) -> None:
    logger = get_activity_logger()
    extra = {"username": username, "action": action}
    msg = details

    lvl = level.upper()
    if lvl == "WARNING":
        logger.warning(msg, extra=extra)
    elif lvl == "ERROR":
        logger.error(msg, extra=extra)
    else:
        logger.info(msg, extra=extra)
