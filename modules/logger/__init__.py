"""
Logging Module

Provides structured logging for the entire system.
"""

import sys
import json
from datetime import datetime
from typing import Any
import logging
import structlog

from .formatter import StructuredFormatter

logger = structlog.get_logger(__name__)


def setup_logging(log_level: str = "INFO", json_format: bool = True):
    """
    Setup structured logging

    Args:
        log_level: Logging level
        json_format: Use JSON format for logs
    """
    log_level = getattr(logging, log_level.upper(), logging.INFO)

    # Create stdout logger
    log_renderer = StructuredFormatter() if json_format else None

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            log_renderer,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logger = structlog.get_logger()

    # Set root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = []

    # Add console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    root_logger.addHandler(handler)

    logger.info("Logging configured", level=log_level, json_format=json_format)


class get_logger:
    """
    Helper function to get a logger for a module

    Usage:
        from modules.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Message", key="value")
    """

    def __init__(self, name: str):
        self._name = name

    def debug(self, message: str, **kwargs: Any):
        logger.debug(message, module=self._name, **kwargs)

    def info(self, message: str, **kwargs: Any):
        logger.info(message, module=self._name, **kwargs)

    def warning(self, message: str, **kwargs: Any):
        logger.warning(message, module=self._name, **kwargs)

    def error(self, message: str, **kwargs: Any):
        logger.error(message, module=self._name, **kwargs)

    def critical(self, message: str, **kwargs: Any):
        logger.critical(message, module=self._name, **kwargs)


__all__ = ["setup_logging", "get_logger"]
