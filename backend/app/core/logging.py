"""Structured JSON logging configuration for OmniPharma.

Configures the root logger with a JSON-line formatter so that every log
record emitted by ``app.*`` modules is machine-parseable. Call
``configure_logging()`` once at application startup (inside
``app.main``'s lifespan handler).

Imports/dependencies: logging, json, app.core.config.

Public outputs: ``configure_logging()``, ``get_logger()``.
"""

import json
import logging
import sys
from datetime import datetime, timezone

from app.core.config import get_settings


class _JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects.

    Each emitted line contains ``timestamp``, ``level``, ``logger``,
    ``message``, and any extra fields attached to the ``LogRecord``.
    """

    def format(self, record: logging.LogRecord) -> str:  # noqa: D102
        payload: dict = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        # Attach any extra keyword arguments passed to the logger call.
        for key, value in record.__dict__.items():
            if key not in logging.LogRecord.__dict__ and not key.startswith("_"):
                payload[key] = value
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """Configure the root logger with a JSON formatter.

    Reads ``log_level`` from :func:`app.core.config.get_settings` and
    applies it to the root logger. Subsequent calls are idempotent.

    Returns:
        None
    """
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())

    root = logging.getLogger()
    if not root.handlers:
        root.addHandler(handler)
    root.setLevel(level)

    # Quieten overly verbose third-party loggers.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger bound to ``name``.

    Args:
        name: Typically ``__name__`` of the calling module.

    Returns:
        A :class:`logging.Logger` that writes JSON-formatted records once
        :func:`configure_logging` has been called.
    """
    return logging.getLogger(name)
