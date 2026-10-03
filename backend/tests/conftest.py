"""Pytest configuration and shared test fixtures."""

import os

import pytest
from starlette.testclient import TestClient

# Ensure test environment variables are set before loading app
os.environ["ENVIRONMENT"] = "testing"
os.environ["DEBUG"] = "false"
os.environ["SECRET_KEY"] = "test_secret_key_at_least_32_characters_long_for_tests"

from app.main import create_app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    """Provide a TestClient instance for testing HTTP endpoints."""
    app = create_app()
    with TestClient(app, base_url="http://testserver") as test_client:
        yield test_client
