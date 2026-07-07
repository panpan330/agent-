import logging
import sys


APP_LOGGER_NAMES = (
    "app",
    "uvicorn",
    "uvicorn.error",
    "uvicorn.access",
)
LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_log_level(log_level: str) -> int:
    level = logging.getLevelName(log_level.upper())
    if not isinstance(level, int):
        raise ValueError(f"Unsupported log level: {log_level}")
    return level


def configure_logging(log_level: str) -> None:
    level = get_log_level(log_level)
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        stream=sys.stdout,
    )

    for logger_name in APP_LOGGER_NAMES:
        logging.getLogger(logger_name).setLevel(level)
