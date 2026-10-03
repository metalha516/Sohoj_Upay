"""User profile, data rights, and GDPR account erasure endpoints per security.md §4 & §12."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status

from app.api.deps import get_current_user, get_user_service, rate_limit_dependency
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.user import (
    UserDataExportResponse,
    UserDeleteRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_my_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    """Retrieve sanitized profile details of the authenticated caller."""
    return await user_service.get_profile(current_user)


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile attributes",
)
async def update_my_profile(
    req: UserUpdateRequest,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    """Update profile fields with strict mass-assignment prevention (extra='forbid')."""
    client_ip = request.client.host if request.client else None
    updated_user = await user_service.update_profile(current_user, req, client_ip=client_ip)
    return UserResponse.model_validate(updated_user)


@router.get(
    "/me/export",
    response_model=UserDataExportResponse,
    dependencies=[Depends(rate_limit_dependency(max_requests=5, window_seconds=300))],
    summary="Export all user data (GDPR / privacy access right)",
)
async def export_my_data(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserDataExportResponse:
    """Export complete structured data portfolio belonging to the authenticated user."""
    client_ip = request.client.host if request.client else None
    return await user_service.export_data(current_user, client_ip=client_ip)


@router.delete(
    "/me",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Permanently delete user account and all personal data",
)
async def delete_my_account(
    req: UserDeleteRequest,
    request: Request,
    response: Response,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> MessageResponse:
    """Permanently delete user account and cascade delete all transactions and goals upon re-auth."""
    client_ip = request.client.host if request.client else None
    await user_service.delete_account(current_user, req.password, client_ip=client_ip)

    # Clear authentication cookie
    response.delete_cookie(key="refresh_token", path="/api/v1/auth")

    return MessageResponse(message="Account and all associated records permanently erased.")
