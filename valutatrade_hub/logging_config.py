import logging
from logging.handlers import RotatingFileHandler
import os

from valutatrade_hub.infra.settings import SettingsLoader



def setup_logging():
    """Настройка логирования"""
    
    settings = SettingsLoader()

    log_dir = settings.get("LOG_DIR")
    log_file = settings.get("LOG_FILE")

    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger("valutatrade")
    logger.setLevel(logging.INFO)

    handler = RotatingFileHandler(
        log_file,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )

    formatter = logging.Formatter(
        fmt="%(levelname)s %(asctime)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.propagate = False

    return logger


LOGGER = setup_logging()
