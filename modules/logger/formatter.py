"""
Structured Logging Formatter

Formats log messages as JSON or human-readable text.
"""

import json
from typing import Any
import structlog
from datetime import datetime


class StructuredFormatter(structlog.processors.JSONRenderer):
    """JSON log formatter"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __call__(
        self,
        logger: str,
        name: str,
        event_dict: dict,
    ) -> str:
        # Add timestamp if not present
        if "timestamp" not in event_dict:
            event_dict["timestamp"] = datetime.utcnow().isoformat()

        # Add log level
        if "level" not in event_dict:
            event_dict["level"] = name.lower()

        # Add service name
        if "service" not in event_dict:
            event_dict["service"] = "cronjob-money-mvp"

        # Format as JSON
        return super().__call__(logger, name, event_dict)


class HumanReadableFormatter(structlog.dev.ConsoleRenderer):
    """Human-readable log formatter"""

    def __init__(self):
        super().__init__(colors=True, include_traceback=True)

    def __call__(
        self,
        logger: str,
        name: str,
        event_dict: dict,
    ) -> str:
        # Format as human-readable
        return super().__call__(logger, name, event_dict)
