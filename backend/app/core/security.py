"""Cryptographic security utilities for authentication and token validation.

Adheres strictly to security.md §3:
- Argon2id password hashing (memory >= 64 MiB, time >= 3, parallelism >= 1).
- Breached password check and minimum 12-character policy.
- Pinned JWT access token generation and strict verification (iss, aud, exp, jti, sub).
- Opaque cryptographically random refresh tokens stored as SHA-256 hashes.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import argon2
import jwt
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import get_settings

# Argon2id password hasher tuned to ASVS L2 / security.md §3 specifications:
# time_cost=3, memory_cost=65536 (64 MiB), parallelism=1
_password_hasher = argon2.PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=1,
    hash_len=32,
    salt_len=16,
    type=argon2.Type.ID,
)

# Curated catalog of top leaked / trivial passwords (> 12 chars or common patterns)
BREACHED_PASSWORD_SAMPLE: frozenset[str] = frozenset(
    {
        "password123456",
        "12345678901234",
        "qwertyuiop1234",
        "password@12345",
        "admin123456789",
        "iloveyou123456",
        "financialcoach1",
        "bangladesh1234",
        "dhakacity12345",
        "welcome1234567",
        "monkey12345678",
        "letmein1234567",
        "sunshine123456",
        "trustnoone1234",
        "supersecret123",
        "changeme123456",
        "correcthorseba",
        "password1234567",
        "123456789012345",
    }
)


def hash_password(password: str) -> str:
    """Hash plaintext password using Argon2id with per-user cryptographic salt."""
    return _password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plaintext password against an Argon2id hash in constant time."""
    try:
        return _password_hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def is_password_breached(password: str) -> bool:
    """Check if password appears in breached password corpus or trivial repetitions."""
    normalized = password.lower().strip()
    if normalized in BREACHED_PASSWORD_SAMPLE:
        return True
    # Detect trivial repeated characters (e.g., 'aaaaaaaaaaaa')
    return len(set(normalized)) <= 2 and len(normalized) >= 12


def validate_password_strength(password: str) -> None:
    """Enforce security.md §3 password policy (min 12 chars, not breached)."""
    if len(password) < 12:
        raise ValueError("Password must be at least 12 characters long.")
    if len(password) > 128:
        raise ValueError("Password cannot exceed 128 characters.")
    if is_password_breached(password):
        raise ValueError("Password is too common or has appeared in known data breaches.")


def generate_refresh_token() -> str:
    """Generate an opaque, cryptographically random refresh token with 256+ bits of entropy."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """Hash refresh token with SHA-256 for server-side persistence."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(
    user_id: uuid.UUID | str,
    extra_claims: dict[str, Any] | None = None,
) -> tuple[str, str, datetime]:
    """Create a signed 15-minute JWT access token with required security claims.

    Claims: sub, iss, aud, exp, iat, nbf, jti.

    Returns:
        tuple of (encoded_jwt_str, jti_str, expires_at_datetime)
    """
    settings = get_settings()
    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=settings.access_token_expire_minutes)
    token_jti = str(uuid.uuid4())

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "jti": token_jti,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }

    if extra_claims:
        for k, v in extra_claims.items():
            if k not in payload:
                payload[k] = v

    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return token, token_jti, expires_at


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token strictly against pinned configuration.

    Strictly rejects:
    - alg=none or mismatched algorithm
    - expired tokens
    - invalid signature
    - invalid audience or issuer
    - missing mandatory claims (sub, exp, iat, jti)
    """
    settings = get_settings()

    # Pre-inspect header to ensure algorithm is strictly pinned
    try:
        header = jwt.get_unverified_header(token)
    except Exception as exc:
        raise jwt.InvalidTokenError(f"Malformed token header: {exc}") from exc

    if header.get("alg") != settings.algorithm:
        raise jwt.InvalidTokenError(
            f"Algorithm '{header.get('alg')}' is not allowed (pinned to '{settings.algorithm}')."
        )

    # Strictly decode and validate claims
    payload: dict[str, Any] = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm],
        audience=settings.jwt_audience,
        issuer=settings.jwt_issuer,
        options={
            "require": ["exp", "iat", "sub", "jti"],
            "verify_exp": True,
            "verify_iat": True,
            "verify_aud": True,
            "verify_iss": True,
        },
    )
    return payload
