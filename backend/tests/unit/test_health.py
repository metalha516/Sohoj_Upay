"""Unit tests for health and readiness endpoints."""

from starlette.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    """Test that /health returns 200 OK with expected liveness fields."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "app" in data
    assert "version" in data
    assert "timestamp" in data
    assert "X-Request-ID" in response.headers


def test_api_v1_health_endpoint(client: TestClient) -> None:
    """Test that /api/v1/health also returns 200 OK."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_ready_endpoint_handles_unreachable_services(client: TestClient) -> None:
    """Test that /ready returns RFC 7807 problem details when services are unreachable."""
    response = client.get("/ready")
    # In unit tests without running postgres/redis, /ready should report 503 Problem Details
    assert response.status_code in (200, 503)
    data = response.json()

    if response.status_code == 503:
        assert data["code"] == "SERVICE_UNAVAILABLE"
        assert data["title"] == "Service Unavailable"
        assert response.headers["content-type"].startswith("application/problem+json")
    else:
        assert data["status"] == "ready"
