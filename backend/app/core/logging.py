"""Structured logging configuration."""

import json
import logging
import sys
import time
import traceback
import uuid
from contextvars import ContextVar
from typing import Any

from backend.app.core.config import settings

# Context variable for request-scoped data (request ID, user, etc.)
_request_context: ContextVar[dict[str, Any]] = ContextVar("request_context", default={})


def get_request_context() -> dict[str, Any]:
    return _request_context.get()


def set_request_context(**kwargs) -> None:
    ctx = _request_context.get().copy()
    ctx.update(kwargs)
    _request_context.set(ctx)


def clear_request_context() -> None:
    _request_context.set({})


def new_request_id() -> str:
    return uuid.uuid4().hex[:12]


class JSONFormatter(logging.Formatter):
    """Format log records as JSON for log aggregation (ELK, Loki, CloudWatch, etc.)."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add request context (request_id, user_id, etc.)
        ctx = _request_context.get()
        if ctx:
            log_entry["context"] = ctx

        # Add exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        # Add extra fields
        for key in ("method", "path", "status_code", "duration_ms", "user_id", "album_id"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        return json.dumps(log_entry, default=str)


class TextFormatter(logging.Formatter):
    """Human-readable format for local development."""

    def format(self, record: logging.LogRecord) -> str:
        ctx = _request_context.get()
        request_id = ctx.get("request_id", "-")
        user_id = ctx.get("user_id", "-")

        base = f"{self.formatTime(record)} [{record.levelname:8s}] [{request_id}] [{user_id}] {record.name}: {record.getMessage()}"

        if record.exc_info and record.exc_info[0] is not None:
            base += "\n" + "".join(traceback.format_exception(*record.exc_info))

        return base


def setup_logging() -> None:
    """
    Configure structured logging for the application.

    - JSON format in production (for log aggregation)
    - Text format in development (for readability)
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Remove existing handlers
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if settings.log_format == "json":
        handler.setFormatter(JSONFormatter(datefmt="%Y-%m-%dT%H:%M:%S"))
    else:
        handler.setFormatter(TextFormatter(datefmt="%Y-%m-%d %H:%M:%S"))

    root_logger.addHandler(handler)

    # Quiet down noisy third-party loggers
    for logger_name in [
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "sqlalchemy",
        "sqlalchemy.engine",
        "sqlalchemy.engine.Engine",
        "sqlalchemy.pool",
        "sqlalchemy.dialects",
        "sqlalchemy.orm",
        "httpx",
        "httpcore",
        "asyncio",
        "aiosqlite",
    ]:
        logging.getLogger(logger_name).setLevel(logging.ERROR)
        logging.getLogger(logger_name).propagate = False


def get_logger(name: str) -> logging.Logger:
    """Get a named logger."""
    return logging.getLogger(name)


# Pre-built loggers for common components
api_logger = get_logger("ratemyalbum.api")
db_logger = get_logger("ratemyalbum.db")
auth_logger = get_logger("ratemyalbum.auth")
elo_logger = get_logger("ratemyalbum.elo")
recommendations_logger = get_logger("ratemyalbum.recommendations")
worker_logger = get_logger("ratemyalbum.worker")
