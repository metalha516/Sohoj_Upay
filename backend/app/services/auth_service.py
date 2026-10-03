"""Authentication service coordinating password hashing, JWTs, rotation, and audit logs."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.rate_limit import lockout_manager
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    validate_password_strength,
    verify_password,
)
from app.models.user import User
from app.repositories.audit_repo import AuditLogRepository
from app.repositories.auth_repo import RefreshTokenRepository
from app.repositories.user_repo import UserRepository
from app.schemas.auth import RegisterRequest


class AuthService:
    """Core authentication logic per security.md §3."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.auth_repo = RefreshTokenRepository(session)
        self.audit_repo = AuditLogRepository(session)
        self.settings = get_settings()

    async def register(
        self,
        req: RegisterRequest,
        client_ip: str | None = None,
    ) -> tuple[User, str, datetime]:
        """Register a new user account with Argon2id password hashing."""
        # 1. Enforce password policy (min 12 chars, not breached)
        try:
            validate_password_strength(req.password)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc

        # 2. Check email uniqueness
        existing = await self.user_repo.get_by_email(req.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email address is already registered.",
            )

        # 3. Hash password using Argon2id
        pw_hash = hash_password(req.password)

        # 4. Create user record
        user = User(
            name=req.name.strip(),
            email=req.email.lower().strip(),
            password_hash=pw_hash,
            monthly_income=req.monthly_income,
            consent_ai=req.consent_ai,
        )
        created_user = await self.user_repo.create(user)

        # 5. Issue initial refresh token
        raw_refresh = generate_refresh_token()
        h_refresh = hash_refresh_token(raw_refresh)
        refresh_expires = datetime.now(UTC) + timedelta(
            days=self.settings.refresh_token_expire_days
        )
        await self.auth_repo.create(h_refresh, created_user.id, refresh_expires)

        # 6. Audit log
        await self.audit_repo.log_event(
            actor=str(created_user.id),
            action="AUTH_REGISTER",
            user_id=created_user.id,
            resource=f"/users/{created_user.id}",
            ip=client_ip,
            metadata={"consent_ai": created_user.consent_ai},
        )

        return created_user, raw_refresh, refresh_expires

    async def login(
        self,
        email: str,
        password: str,
        client_ip: str | None = None,
    ) -> tuple[User, str, str, int, datetime]:
        """Authenticate user credentials and issue token pair."""
        clean_email = email.lower().strip()

        # 1. Check account & IP lockout
        is_locked, retry_after = await lockout_manager.check_lockout(clean_email)
        if is_locked:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Account temporarily locked due to repeated failed logins. Retry after {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)},
            )

        if client_ip:
            ip_locked, ip_retry = await lockout_manager.check_lockout(client_ip)
            if ip_locked:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many failed login attempts from this IP. Retry after {ip_retry} seconds.",
                    headers={"Retry-After": str(ip_retry)},
                )

        # 2. Fetch user
        user = await self.user_repo.get_by_email(clean_email)
        if not user:
            # Record failure against email & IP to prevent user enumeration
            await lockout_manager.record_failure(clean_email)
            if client_ip:
                await lockout_manager.record_failure(client_ip)
            await self.audit_repo.log_event(
                actor="anonymous",
                action="AUTH_LOGIN_FAILURE",
                ip=client_ip,
                metadata={"reason": "user_not_found"},
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 3. Verify password hash using Argon2id in constant time
        if not verify_password(password, user.password_hash):
            failures, locked_now = await lockout_manager.record_failure(clean_email)
            if client_ip:
                await lockout_manager.record_failure(client_ip)
            await self.audit_repo.log_event(
                actor=str(user.id),
                action="AUTH_LOGIN_FAILURE",
                user_id=user.id,
                ip=client_ip,
                metadata={"reason": "invalid_password", "failures": failures, "locked": locked_now},
            )
            if locked_now:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Account locked due to consecutive failed attempts. Please try again later.",
                )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 4. Successful login: reset failed counters
        await lockout_manager.reset_failures(clean_email)
        if client_ip:
            await lockout_manager.reset_failures(client_ip)

        # 5. Create access token & refresh token
        access_token, _, _ = create_access_token(user.id)
        raw_refresh = generate_refresh_token()
        h_refresh = hash_refresh_token(raw_refresh)
        refresh_expires = datetime.now(UTC) + timedelta(
            days=self.settings.refresh_token_expire_days
        )
        await self.auth_repo.create(h_refresh, user.id, refresh_expires)

        # 6. Audit log
        await self.audit_repo.log_event(
            actor=str(user.id),
            action="AUTH_LOGIN_SUCCESS",
            user_id=user.id,
            ip=client_ip,
        )

        expires_in = self.settings.access_token_expire_minutes * 60
        return user, access_token, raw_refresh, expires_in, refresh_expires

    async def refresh(
        self,
        raw_refresh_token: str,
        client_ip: str | None = None,
    ) -> tuple[User, str, str, int, datetime]:
        """Rotate refresh token with reuse detection per security.md §3."""
        if not raw_refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token required.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        h_token = hash_refresh_token(raw_refresh_token)
        token_record = await self.auth_repo.get_by_hash(h_token)

        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # --- REUSE DETECTION ---
        # If token was already revoked, a threat actor has stolen an older rotated token!
        if token_record.revoked:
            user_id = token_record.user_id
            # Invalidate all active tokens for this user family immediately
            revoked_count = await self.auth_repo.revoke_all_for_user(user_id)
            await self.audit_repo.log_event(
                actor=str(user_id),
                action="AUTH_REFRESH_REUSE_DETECTED",
                user_id=user_id,
                ip=client_ip,
                metadata={"revoked_sessions_count": revoked_count},
            )
            await self.session.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token reuse detected. All sessions have been revoked.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Expiry check
        now = datetime.now(UTC)
        record_exp = token_record.expires_at
        if record_exp.tzinfo is None:
            record_exp = record_exp.replace(tzinfo=UTC)
        if record_exp <= now:
            await self.auth_repo.revoke(token_record)
            await self.session.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Normal Rotation: revoke current token
        await self.auth_repo.revoke(token_record)

        # Fetch user
        user = await self.user_repo.get_by_id_for_user(token_record.user_id, token_record.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account no longer exists.",
            )

        # Issue replacement access token & refresh token
        new_access_token, _, _ = create_access_token(user.id)
        new_raw_refresh = generate_refresh_token()
        new_h_refresh = hash_refresh_token(new_raw_refresh)
        new_refresh_expires = now + timedelta(days=self.settings.refresh_token_expire_days)
        await self.auth_repo.create(new_h_refresh, user.id, new_refresh_expires)

        # Audit log
        await self.audit_repo.log_event(
            actor=str(user.id),
            action="AUTH_REFRESH_SUCCESS",
            user_id=user.id,
            ip=client_ip,
        )

        expires_in = self.settings.access_token_expire_minutes * 60
        return user, new_access_token, new_raw_refresh, expires_in, new_refresh_expires

    async def logout(
        self,
        user_id: uuid.UUID,
        raw_refresh_token: str | None = None,
        client_ip: str | None = None,
    ) -> None:
        """Revoke refresh tokens and log out session."""
        if raw_refresh_token:
            h_token = hash_refresh_token(raw_refresh_token)
            record = await self.auth_repo.get_by_hash(h_token)
            if record:
                await self.auth_repo.revoke(record)
        else:
            await self.auth_repo.revoke_all_for_user(user_id)

        await self.audit_repo.log_event(
            actor=str(user_id),
            action="AUTH_LOGOUT",
            user_id=user_id,
            ip=client_ip,
        )

    async def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str,
        client_ip: str | None = None,
    ) -> None:
        """Change password with verification, strength validation, and family revocation."""
        # 1. Verify current password
        if not verify_password(current_password, user.password_hash):
            await self.audit_repo.log_event(
                actor=str(user.id),
                action="AUTH_PASSWORD_CHANGE_FAILURE",
                user_id=user.id,
                ip=client_ip,
                metadata={"reason": "invalid_current_password"},
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect.",
            )

        # 2. Validate new password strength
        try:
            validate_password_strength(new_password)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc

        if new_password == current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password.",
            )

        # 3. Hash new password & update
        user.password_hash = hash_password(new_password)
        await self.session.flush()

        # 4. Invalidate all existing refresh tokens (forces re-auth across all devices)
        await self.auth_repo.revoke_all_for_user(user.id)

        # 5. Audit log
        await self.audit_repo.log_event(
            actor=str(user.id),
            action="AUTH_PASSWORD_CHANGE_SUCCESS",
            user_id=user.id,
            ip=client_ip,
        )
