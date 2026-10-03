"""Structured JSON logging with request correlation IDs and log scrubbing."""

import json
import logging
import re
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

# Context variable to hold the active request ID across async tasks
request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="")

# Sensitive patterns to scrub from log messages
SENSITIVE_PATTERNS = [
    (
        re.compile(
            r'(?i)("?(?:password|token|secret|authorization|api_key|access_token|refresh_token)"?\s*[:=]\s*["\'])([^"\']+)(["\'])'
        ),
        r"\1[REDACTED]\3",
    ),
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9\-\._~\+\/]+=*"), "Bearer [REDACTED]"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"), "[REDACTED_EMAIL]"),
    (re.compile(r"(?:\+?8801|01)[3-9]\d{8}"), "[REDACTED_PHONE]"),
]


def scrub_message(message: str) -> str:
    """Scrub sensitive information such as tokens, passwords, emails, and phone numbers from logs."""
    for pattern, replacement in SENSITIVE_PATTERNS:
        message = pattern.sub(replacement, message)
    return message


class JSONFormatter(logging.Formatter):
    """Custom logging formatter that outputs logs as structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": scrub_message(record.getMessage()),
            "request_id": request_id_ctx_var.get() or getattr(record, "request_id", ""),
        }

        # Include standard extra fields if present
        for key in ("route", "status", "latency_ms", "user_hash", "client_ip"):
            if hasattr(record, key):
                log_obj[key] = getattr(record, key)

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj, ensure_ascii=False)


def setup_logging(log_level: str = "INFO") -> None:
    """Configure structured JSON logging for the application."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove existing handlers to avoid duplicates
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)

    # Silence overly verbose external loggers
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.access").propagate = True
