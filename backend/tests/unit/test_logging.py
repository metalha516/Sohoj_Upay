"""Unit tests for structured logging and log scrubbing."""

import json
import logging

from app.core.logging import JSONFormatter, scrub_message


def test_scrub_message_removes_sensitive_data() -> None:
    """Verify that scrub_message scrubs passwords, tokens, emails, and phone numbers."""
    raw_message = (
        'User login failed with password="SecretPassword123" and token="eyJh...". '
        "Contact email: john.doe@example.com, phone: 01712345678, header: Bearer abcdef12345"
    )
    scrubbed = scrub_message(raw_message)

    assert "SecretPassword123" not in scrubbed
    assert "john.doe@example.com" not in scrubbed
    assert "01712345678" not in scrubbed
    assert "abcdef12345" not in scrubbed
    assert "[REDACTED]" in scrubbed
    assert "[REDACTED_EMAIL]" in scrubbed
    assert "[REDACTED_PHONE]" in scrubbed


def test_json_formatter_outputs_valid_json() -> None:
    """Verify that JSONFormatter formats LogRecord into valid JSON with expected fields."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Transaction processed for user with password='mypassword'",
        args=(),
        exc_info=None,
    )
    record.request_id = "req-12345"  # type: ignore[attr-defined]

    formatted_str = formatter.format(record)
    parsed = json.loads(formatted_str)

    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test_logger"
    assert parsed["request_id"] == "req-12345"
    assert "mypassword" not in parsed["message"]
    assert "[REDACTED]" in parsed["message"]
