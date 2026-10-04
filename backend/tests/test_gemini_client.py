"""Forwarding shim for test_gemini_client.py to tests/unit/test_gemini_client.py."""

from tests.unit.test_gemini_client import (
    test_gemini_complete_function_call,
    test_gemini_complete_text_response,
    test_gemini_missing_api_key_raises,
)

__all__ = [
    "test_gemini_missing_api_key_raises",
    "test_gemini_complete_text_response",
    "test_gemini_complete_function_call",
]
