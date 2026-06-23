"""JSON-structured logging using only the stdlib `logging` module."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any, ClassVar

__all__ = ["JsonFormatter", "get_logger", "log_with_context"]


class JsonFormatter(logging.Formatter):
    """Format every log record as a single canonical JSON object."""

    _RESERVED: ClassVar[set[str]] = {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "taskName",
        "message",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC)
            .isoformat()
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Promote any extra fields the caller attached.
        for key, value in record.__dict__.items():
            if key in self._RESERVED or key.startswith("_"):
                continue
            payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, sort_keys=True, default=str)


def get_logger(name: str) -> logging.Logger:
    """Return a logger configured with the JSON formatter on stderr.

    Idempotent: repeated calls with the same name do not stack handlers.
    """
    logger = logging.getLogger(name)
    if not any(getattr(h, "_paper1_json", False) for h in logger.handlers):
        handler = logging.StreamHandler(stream=sys.stderr)
        handler.setFormatter(JsonFormatter())
        handler._paper1_json = True  # type: ignore[attr-defined]
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def log_with_context(logger: logging.Logger, level: int, msg: str, **context: Any) -> None:
    """Emit a log record with arbitrary structured context fields."""
    logger.log(level, msg, extra=context)
