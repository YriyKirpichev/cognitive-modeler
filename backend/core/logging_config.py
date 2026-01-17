import logging.config
import os

LOG_DIR = "logs"
APP_LOG_FILE = os.path.join(LOG_DIR, "app.log")
TEST_LOG_FILE = os.path.join(LOG_DIR, "test.log")

os.makedirs(LOG_DIR, exist_ok=True)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(levelname)s - %(message)s",
        }
    },
    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "default",
            "encoding": "utf-8",
            "maxBytes": 10485760,  # 10 MB
            "backupCount": 5,
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "loggers": {
        "app": {
            "level": "DEBUG",
            "handlers": ["file", "console"],
            "propagate": False,
        },
    },
}


def setup_logging():
    is_testing = "pytest" in os.environ.get("_", "")
    log_file = TEST_LOG_FILE if is_testing else APP_LOG_FILE
    LOGGING_CONFIG["handlers"]["file"]["filename"] = log_file
    logging.config.dictConfig(LOGGING_CONFIG)
