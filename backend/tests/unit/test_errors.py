"""Unit tests for RFC 7807 Problem Details and error handlers."""

from starlette.testclient import TestClient


def test_404_returns_rfc7807_problem_details(client: TestClient) -> None:
    """Test that requesting an undefined route returns RFC 7807 problem+json response."""
    response = client.get("/non-existent-endpoint")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")

    data = response.json()
    assert data["type"] == "about:blank"
    assert data["title"] == "Not Found"
    assert data["status"] == 404
    assert data["code"] == "HTTP_404"
    assert data["instance"] == "/non-existent-endpoint"
    assert "detail" in data
    assert "request_id" in data


def test_security_headers_present_on_all_responses(client: TestClient) -> None:
    """Test that baseline security headers are attached by middleware."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Cache-Control") == "no-store"
    assert "X-Request-ID" in response.headers
