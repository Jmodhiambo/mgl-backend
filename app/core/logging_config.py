#!/usr/bin/env python
"""Logging configuration for MGLTickets."""

import logging
import json
from logging.handlers import RotatingFileHandler
from pathlib import Path
from contextvars import ContextVar


# Context variables for request-scoped logging
user_id_var: ContextVar[str] = ContextVar("user_id", default="anonymous")
role_var: ContextVar[str] = ContextVar("role", default="guest")


class ContextFilter(logging.Filter):
    """Injects user-specific context vars into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.user_id = user_id_var.get()
        record.role = role_var.get()
        return True


class JSONFormatter(logging.Formatter):
    """Formatter that outputs logs in structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "user_id": getattr(record, "user_id", "unknown"),
            "role": getattr(record, "role", "unknown"),
            "message": record.getMessage(),
        }

        # Include any custom extra fields
        if record.__dict__.get("extra", None):
            log_data.update(record.__dict__["extra"])

        return json.dumps(log_data)


def configure_logging() -> None:
    """Configure the application logging system with JSON logs."""

    logs_dir = Path("app/logs/")
    logs_dir.mkdir(exist_ok=True)

    log_file = logs_dir / "app.jsonl"  # JSON lines file

    file_handler = RotatingFileHandler(
        filename=str(log_file),
        maxBytes=5_000_000,  # 5 MB
        backupCount=5,
    )
    file_handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addFilter(ContextFilter())


# App-level logger
logger = logging.getLogger("MGLTicketsLogger")