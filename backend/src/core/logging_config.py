"""Logging configuration for the application"""

import logging
import logging.config
import sys
from typing import Any

from pydantic import BaseModel


class LogConfig(BaseModel):
    """Logging configuration schema"""

    LOGGER_NAME: str = "twitter_scraping_saas"
    LOG_FORMAT: str = "%(levelprefix)s | %(asctime)s | %(name)s | %(message)s"
    LOG_LEVEL: str = "INFO"

    # Logging config
    version: int = 1
    disable_existing_loggers: bool = False
    formatters: dict[str, dict[str, Any]] = {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }
    handlers: dict[str, dict[str, Any]] = {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    }
    loggers: dict[str, dict[str, Any]] = {
        LOGGER_NAME: {"handlers": ["default"], "level": LOG_LEVEL},
    }


def setup_logging(log_level: str = "INFO") -> None:
    """Setup logging configuration"""
    log_config = LogConfig(LOG_LEVEL=log_level)
    logging.config.dictConfig(log_config.model_dump())


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(f"twitter_scraping_saas.{name}")
