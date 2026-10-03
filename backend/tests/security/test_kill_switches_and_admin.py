"""Integration tests for emergency kill switches and administrative token revocation."""

import uuid
import pytest
from starlette.testclient import TestClient
from app.core.config import get_settings


def test_registration_kill_switch(client: TestClient, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "registration_enabled", False)

    res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "disabled@example.com",
            "password": "Password12345!",
            "name": "Disabled Test",
        },
    )
    assert res.status_code == 503
    data = res.json()
    assert "registration is currently disabled" in data["detail"]


def test_login_kill_switch(client: TestClient, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "login_enabled", False)

    res = client.post(
        "/api/v1/auth/login",
        json={
            "email": "user@example.com",
            "password": "Password12345!",
        },
    )
    assert res.status_code == 503
    data = res.json()
    assert "authentication is currently disabled" in data["detail"]


def test_ai_kill_switch(client: TestClient, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "ai_enabled", False)

    # First register and login a user to get valid token
    monkeypatch.setattr(settings, "registration_enabled", True)
    monkeypatch.setattr(settings, "login_enabled", True)

    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": "ai.kill@example.com",
            "password": "SecurePassword123!",
            "name": "AI Kill Test",
            "consent_ai": True,
        },
    )
    assert reg.status_code == 201

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "ai.kill@example.com", "password": "SecurePassword123!"},
    )
    token = login_res.json()["access_token"]

    # Now disable AI
    monkeypatch.setattr(settings, "ai_enabled", False)

    res = client.post(
        "/api/v1/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Can I afford 5000?"},
    )
    assert res.status_code == 503
    assert "Conversational AI services are currently disabled" in res.json()["detail"]


def test_forecast_kill_switch(client: TestClient, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "registration_enabled", True)
    monkeypatch.setattr(settings, "login_enabled", True)

    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": "fc.kill@example.com",
            "password": "SecurePassword123!",
            "name": "Forecast Kill Test",
        },
    )
    assert reg.status_code == 201

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "fc.kill@example.com", "password": "SecurePassword123!"},
    )
    token = login_res.json()["access_token"]

    monkeypatch.setattr(settings, "forecast_enabled", False)

    res = client.get(
        "/api/v1/forecast/expenses",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 503
    assert "Financial forecasting services are currently disabled" in res.json()["detail"]


def test_admin_token_revocation_unauthorized(client: TestClient):
    # No admin key header
    res = client.post(
        "/api/v1/admin/revoke-tokens",
        json={"all_users": True, "reason": "Testing"},
    )
    assert res.status_code == 403
    assert "Valid administrative authorization" in res.json()["detail"]

    # Wrong admin key header
    res_wrong = client.post(
        "/api/v1/admin/revoke-tokens",
        headers={"X-Admin-Key": "incorrect_key"},
        json={"all_users": True, "reason": "Testing"},
    )
    assert res_wrong.status_code == 403


def test_admin_token_revocation_authorized(client: TestClient):
    settings = get_settings()
    admin_key = settings.admin_api_key

    target_uid = str(uuid.uuid4())
    res = client.post(
        "/api/v1/admin/revoke-tokens",
        headers={"X-Admin-Key": admin_key},
        json={"user_id": target_uid, "reason": "Security incident drill"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "revoked"
    assert data["user_id"] == target_uid
    assert data["all_users"] is False

    # Global revocation
    res_global = client.post(
        "/api/v1/admin/revoke-tokens",
        headers={"X-Admin-Key": admin_key},
        json={"all_users": True, "reason": "Global security lockdown drill"},
    )
    assert res_global.status_code == 200
    data_global = res_global.json()
    assert data_global["status"] == "revoked"
    assert data_global["all_users"] is True
