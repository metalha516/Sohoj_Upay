"""Authentication endpoints per security.md §3."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status

from app.api.deps import get_auth_service, get_current_user, rate_limit_dependency
from app.core.config import get_settings
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    PasswordChangeRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _set_refresh_cookie(response: Response, raw_refresh: str, max_age_days: int) -> None:
    """Set hardened HttpOnly; Secure; SameSite=Lax refresh token cookie per security.md §3."""
    settings = get_settings()
    is_secure = settings.environment in ("production", "staging")
    response.set_cookie(
        key="refresh_token",
        value=raw_refresh,
        max_age=max_age_days * 86400,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        path="/",
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Clear refresh token cookie upon logout or password reset."""
    response.delete_cookie(
        key="refresh_token",
        path="/",
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_dependency(max_requests=5, window_seconds=60))],
    summary="Register new user account",
)
async def register(
    req: RegisterRequest,
    request: Request,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    """Register a new user account with Argon2id hashing and cookie-based refresh token."""
    settings = get_settings()
    if not settings.registration_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User registration is currently disabled by administrator.",
        )

    client_ip = request.client.host if request.client else None
    user, raw_refresh, _ = await auth_service.register(req, client_ip=client_ip)

    # Set hardened refresh cookie
    _set_refresh_cookie(response, raw_refresh, auth_service.settings.refresh_token_expire_days)

    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit_dependency(max_requests=10, window_seconds=60))],
    summary="Authenticate user and issue token pair",
)
async def login(
    req: LoginRequest,
    request: Request,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """Authenticate credentials and issue 15-minute access token + HttpOnly refresh cookie."""
    settings = get_settings()
    if not settings.login_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User authentication is currently disabled by administrator.",
        )

    client_ip = request.client.host if request.client else None
    _, access_token, raw_refresh, expires_in, _ = await auth_service.login(
        req.email, req.password, client_ip=client_ip
    )

    _set_refresh_cookie(response, raw_refresh, auth_service.settings.refresh_token_expire_days)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotate refresh token and issue new access token",
)
async def refresh_token(
    request: Request,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    cookie_token: Annotated[str | None, Cookie(alias="refresh_token")] = None,
) -> TokenResponse:
    """Rotate refresh token. Detects token reuse and revokes entire family if compromised."""
    client_ip = request.client.host if request.client else None
    raw_token = cookie_token

    # Allow fallback if supplied in custom header
    if not raw_token:
        raw_token = request.headers.get("X-Refresh-Token")

    _, new_access, new_refresh, expires_in, _ = await auth_service.refresh(
        raw_token or "", client_ip=client_ip
    )

    _set_refresh_cookie(response, new_refresh, auth_service.settings.refresh_token_expire_days)

    return TokenResponse(
        access_token=new_access,
        token_type="bearer",
        expires_in=expires_in,
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Invalidate session and clear refresh cookie",
)
async def logout(
    request: Request,
    response: Response,
    current_user: Annotated[User, Depends(get_current_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    cookie_token: Annotated[str | None, Cookie(alias="refresh_token")] = None,
) -> MessageResponse:
    """Revoke refresh token and terminate active session."""
    client_ip = request.client.host if request.client else None
    await auth_service.logout(current_user.id, cookie_token, client_ip=client_ip)
    _clear_refresh_cookie(response)
    return MessageResponse(message="Successfully logged out.")


@router.post(
    "/password/change",
    response_model=MessageResponse,
    summary="Change password and force re-authentication across all devices",
)
@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change password (alias) and force re-authentication across all devices",
)
async def change_password(
    req: PasswordChangeRequest,
    request: Request,
    response: Response,
    current_user: Annotated[User, Depends(get_current_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    """Change user password, enforce complexity/breach check, and revoke all active tokens."""
    client_ip = request.client.host if request.client else None
    await auth_service.change_password(
        current_user,
        req.current_password,
        req.new_password,
        client_ip=client_ip,
    )
    _clear_refresh_cookie(response)
    return MessageResponse(
        message="Password updated successfully. Please log in with your new credentials."
    )
