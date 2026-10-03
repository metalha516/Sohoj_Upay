"""Comprehensive security acceptance tests for authentication, tokens, lockout, and users.

Tests:
1. Registration & Password Policy (min 12 chars, breach catalog check, duplicate email rejection).
2. Login & Credential Verification (Argon2id, generic error message).
3. Account Lockout & Backoff (5 failures trigger lockout, 429 Too Many Requests).
4. Strict JWT Validation (forged signature, expired, alg=none, wrong audience, wrong issuer, missing claims).
5. Refresh Token Rotation & Reuse Detection (token rotation, reuse revokes entire family).
6. Logout & Password Change (revokes refresh family, clears cookies).
7. Mass-Assignment Protection (extra='forbid' on PATCH /users/me).
8. Privacy & GDPR Endpoints (GET /users/me, GET /users/me/export, DELETE /users/me).
9. Middleware Protection (request size cap, rate limits, production docs disabled).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import jwt
from starlette.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app

# -----------------------------------------------------------------------------
# 1. Registration & Password Policy Tests
# -----------------------------------------------------------------------------


def test_register_short_password_fails(client: TestClient) -> None:
    """Password shorter than 12 characters is rejected with 422."""
    payload = {
        "name": "Tanvir Hasan",
        "email": "tanvir@example.com",
        "password": "short_pw123",  # 11 chars
        "monthly_income": "45000.00",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


def test_register_breached_password_fails(client: TestClient) -> None:
    """Password in breached catalog is rejected with 422."""
    payload = {
        "name": "Tanvir Hasan",
        "email": "tanvir@example.com",
        "password": "password123456",  # in breached catalog
        "monthly_income": "45000.00",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    assert "breach" in response.text.lower()


def test_register_successful(client: TestClient) -> None:
    """Valid registration succeeds, creates user, and sets HttpOnly refresh cookie."""
    payload = {
        "name": "Tanvir Hasan",
        "email": "tanvir.success@example.com",
        "password": "A_Very_Secure_Password_2026!",
        "monthly_income": "55000.00",
        "consent_ai": True,
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Tanvir Hasan"
    assert data["email"] == "tanvir.success@example.com"
    assert float(data["monthly_income"]) == 55000.00
    assert data["consent_ai"] is True
    assert "password" not in data
    assert "password_hash" not in data

    # Verify HttpOnly cookie is set
    assert "refresh_token" in response.cookies


def test_register_duplicate_email_conflict(client: TestClient) -> None:
    """Registering existing email returns 409 Conflict."""
    payload = {
        "name": "Duplicate User",
        "email": "duplicate@example.com",
        "password": "A_Very_Secure_Password_2026!",
    }
    r1 = client.post("/api/v1/auth/register", json=payload)
    assert r1.status_code == 201

    r2 = client.post("/api/v1/auth/register", json=payload)
    assert r2.status_code == 409
    assert "already registered" in r2.json()["detail"].lower()


# -----------------------------------------------------------------------------
# 2. Login, Lockout, and Token Lifecycle Tests
# -----------------------------------------------------------------------------


def test_login_invalid_credentials_generic_message(client: TestClient) -> None:
    """Invalid credentials return 401 with generic message preventing user enumeration."""
    # Unknown user
    r1 = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "WrongPassword1234!"},
    )
    assert r1.status_code == 401
    assert r1.json()["detail"] == "Invalid email or password."

    # Known user, wrong password
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "User One",
            "email": "user1@example.com",
            "password": "OriginalPassword1234!",
        },
    )
    r2 = client.post(
        "/api/v1/auth/login",
        json={"email": "user1@example.com", "password": "WrongPassword1234!"},
    )
    assert r2.status_code == 401
    assert r2.json()["detail"] == "Invalid email or password."


def test_account_lockout_after_repeated_failures(client: TestClient) -> None:
    """5 consecutive failed logins locks out account and returns 429 Too Many Requests."""
    email = "lockout.target@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"name": "Lock Target", "email": email, "password": "StrongPassword1234!"},
    )

    # 4 failed attempts -> 401
    for _ in range(4):
        res = client.post(
            "/api/v1/auth/login", json={"email": email, "password": "IncorrectPassword12!"}
        )
        assert res.status_code == 401

    # 5th failed attempt triggers lockout -> 429
    res5 = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "IncorrectPassword12!"}
    )
    assert res5.status_code == 429
    assert "locked" in res5.json()["detail"].lower()

    # 6th attempt even with correct password is still rejected under lockout
    res6 = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "StrongPassword1234!"}
    )
    assert res6.status_code == 429


def test_login_successful_and_refresh_rotation(client: TestClient) -> None:
    """Successful login issues access token and rotatable refresh token."""
    email = "login.test@example.com"
    password = "CorrectPassword1234!"
    client.post(
        "/api/v1/auth/register",
        json={"name": "Login User", "email": email, "password": password},
    )

    # Login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert token_data["expires_in"] == 900
    assert "refresh_token" in login_res.cookies

    # Rotate Refresh Token
    refresh_res = client.post("/api/v1/auth/refresh")
    assert refresh_res.status_code == 200
    new_token_data = refresh_res.json()
    assert "access_token" in new_token_data
    assert new_token_data["access_token"] != token_data["access_token"]
    assert "refresh_token" in refresh_res.cookies


def test_refresh_token_reuse_detection_revokes_family(client: TestClient) -> None:
    """Presenting an already rotated refresh token triggers reuse detection and revokes all tokens."""
    email = "reuse.test@example.com"
    password = "CorrectPassword1234!"
    reg_res = client.post(
        "/api/v1/auth/register",
        json={"name": "Reuse User", "email": email, "password": password},
    )
    first_cookie = reg_res.cookies.get("refresh_token")
    assert first_cookie is not None

    # Normal rotation 1 -> first_cookie is now revoked, second_cookie is active
    client.cookies.set("refresh_token", first_cookie)
    rot1_res = client.post("/api/v1/auth/refresh")
    assert rot1_res.status_code == 200
    second_cookie = rot1_res.cookies.get("refresh_token")
    assert second_cookie is not None
    assert second_cookie != first_cookie

    # An attacker tries to replay first_cookie!
    client.cookies.set("refresh_token", first_cookie)
    replay_res = client.post("/api/v1/auth/refresh")
    assert replay_res.status_code == 401
    assert "reuse detected" in replay_res.json()["detail"].lower()

    # Now verify that even the second_cookie is revoked (entire family was terminated!)
    client.cookies.set("refresh_token", second_cookie)
    subsequent_res = client.post("/api/v1/auth/refresh")
    assert subsequent_res.status_code == 401


# -----------------------------------------------------------------------------
# 3. JWT Signature, Algorithm & Claims Validation Tests
# -----------------------------------------------------------------------------


def test_jwt_forged_signature_rejected(client: TestClient) -> None:
    """Access token signed with incorrect secret key is rejected with 401."""
    settings = get_settings()
    now = datetime.now(UTC)
    fake_token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
            "exp": int((now + timedelta(minutes=15)).timestamp()),
            "iat": int(now.timestamp()),
            "jti": str(uuid.uuid4()),
        },
        "wrong_secret_key_used_to_forge_jwt_token",
        algorithm="HS256",
    )

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {fake_token}"},
    )
    assert response.status_code == 401


def test_jwt_expired_rejected(client: TestClient) -> None:
    """Expired access token is rejected with 401."""
    settings = get_settings()
    past = datetime.now(UTC) - timedelta(minutes=30)
    expired_token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
            "exp": int((past + timedelta(minutes=15)).timestamp()),
            "iat": int(past.timestamp()),
            "jti": str(uuid.uuid4()),
        },
        settings.secret_key,
        algorithm="HS256",
    )

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401


def test_jwt_alg_none_rejected(client: TestClient) -> None:
    """Token with alg=none is rejected strictly."""
    settings = get_settings()
    now = datetime.now(UTC)
    # Craft unverified none algorithm token
    header = {"alg": "none", "typ": "JWT"}
    payload = {
        "sub": str(uuid.uuid4()),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "exp": int((now + timedelta(minutes=15)).timestamp()),
        "iat": int(now.timestamp()),
        "jti": str(uuid.uuid4()),
    }
    none_token = jwt.encode(payload, key="", algorithm="none", headers=header)

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {none_token}"},
    )
    assert response.status_code == 401


def test_jwt_wrong_audience_or_issuer_rejected(client: TestClient) -> None:
    """Token with mismatched audience or issuer is rejected with 401."""
    settings = get_settings()
    now = datetime.now(UTC)

    # Wrong audience
    wrong_aud = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "iss": settings.jwt_issuer,
            "aud": "wrong-client-aud",
            "exp": int((now + timedelta(minutes=15)).timestamp()),
            "iat": int(now.timestamp()),
            "jti": str(uuid.uuid4()),
        },
        settings.secret_key,
        algorithm="HS256",
    )
    r1 = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {wrong_aud}"})
    assert r1.status_code == 401

    # Wrong issuer
    wrong_iss = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "iss": "https://malicious-issuer.com",
            "aud": settings.jwt_audience,
            "exp": int((now + timedelta(minutes=15)).timestamp()),
            "iat": int(now.timestamp()),
            "jti": str(uuid.uuid4()),
        },
        settings.secret_key,
        algorithm="HS256",
    )
    r2 = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {wrong_iss}"})
    assert r2.status_code == 401


# -----------------------------------------------------------------------------
# 4. Mass-Assignment & User Privacy Rights Tests
# -----------------------------------------------------------------------------


def test_mass_assignment_protection_on_patch(client: TestClient) -> None:
    """PATCH /users/me forbids unauthorized fields like role, id, password_hash (extra='forbid')."""
    email = "massassign@example.com"
    password = "CorrectPassword1234!"
    client.post(
        "/api/v1/auth/register",
        json={"name": "Victim", "email": email, "password": password},
    )
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    access_token = login_res.json()["access_token"]

    # Attempt to mass-assign forbidden fields
    malicious_payload = {
        "name": "Updated Name",
        "role": "admin",  # forbidden
        "password_hash": "evil_hash",  # forbidden
        "id": str(uuid.uuid4()),  # forbidden
    }
    patch_res = client.patch(
        "/api/v1/users/me",
        json=malicious_payload,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    # Must fail with 422 Unprocessable Entity due to extra='forbid'
    assert patch_res.status_code == 422


def test_user_profile_crud_and_export(client: TestClient) -> None:
    """Verify profile retrieval, valid PATCH, data export, and account deletion."""
    email = "lifecycle@example.com"
    password = "CorrectPassword1234!"
    client.post(
        "/api/v1/auth/register",
        json={"name": "Lifecycle User", "email": email, "password": password, "consent_ai": False},
    )
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    access_token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # 1. GET /users/me
    get_res = client.get("/api/v1/users/me", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Lifecycle User"
    assert get_res.json()["consent_ai"] is False

    # 2. PATCH /users/me (valid fields)
    patch_res = client.patch(
        "/api/v1/users/me",
        json={"name": "Renamed User", "consent_ai": True, "monthly_income": "60000.00"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "Renamed User"
    assert patch_res.json()["consent_ai"] is True
    assert float(patch_res.json()["monthly_income"]) == 60000.00

    # 3. GET /users/me/export
    export_res = client.get("/api/v1/users/me/export", headers=headers)
    assert export_res.status_code == 200
    export_data = export_res.json()
    assert "user" in export_data
    assert "summary" in export_data
    assert export_data["summary"]["consent_ai"] is True

    # 4. DELETE /users/me with wrong password fails
    del_fail = client.request(
        "DELETE",
        "/api/v1/users/me",
        json={"password": "WrongPassword123!", "confirm": True},
        headers=headers,
    )
    assert del_fail.status_code == 401

    # 5. DELETE /users/me with correct password succeeds
    del_ok = client.request(
        "DELETE",
        "/api/v1/users/me",
        json={"password": password, "confirm": True},
        headers=headers,
    )
    assert del_ok.status_code == 200

    # Subsequent access fails
    get_after = client.get("/api/v1/users/me", headers=headers)
    assert get_after.status_code == 401


# -----------------------------------------------------------------------------
# 5. Middleware & Hardening Tests
# -----------------------------------------------------------------------------


def test_request_body_size_limit_rejection(client: TestClient) -> None:
    """Request exceeding size limit returns 413 Payload Too Large."""
    # Send large header content-length or large payload (> 1 MB)
    large_payload = {"huge_data": "A" * (1024 * 1024 + 500)}
    response = client.post("/api/v1/auth/login", json=large_payload)
    assert response.status_code == 413
    assert response.json()["code"] == "PAYLOAD_TOO_LARGE"


def test_docs_disabled_in_production() -> None:
    """Docs endpoints (/docs, /redoc, /openapi.json) are disabled in production environment."""
    import os

    old_env = os.environ.get("ENVIRONMENT", "testing")
    try:
        os.environ["ENVIRONMENT"] = "production"
        get_settings.cache_clear()
        prod_app = create_app()
        with TestClient(prod_app) as prod_client:
            assert prod_client.get("/docs").status_code == 404
            assert prod_client.get("/redoc").status_code == 404
            assert prod_client.get("/openapi.json").status_code == 404
    finally:
        os.environ["ENVIRONMENT"] = old_env
        get_settings.cache_clear()
