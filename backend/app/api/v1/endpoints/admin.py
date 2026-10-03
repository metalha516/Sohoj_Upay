"""Administrative endpoints for emergency kill switches and security token revocation."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import get_settings
from app.core.metrics import AUTH_REFRESH_TOKEN_REUSE_TOTAL
from app.repositories.auth_repo import RefreshTokenRepository
from app.schemas.admin import TokenRevocationRequest, TokenRevocationResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Administration"])


def verify_admin_key(
    x_admin_key: Annotated[str | None, Header(alias="X-Admin-Key")] = None,
) -> bool:
    """Authenticate administrative caller via dedicated high-entropy secret."""
    settings = get_settings()
    configured_key = settings.admin_api_key

    if not x_admin_key or not configured_key or x_admin_key != configured_key:
        logger.warning("Unauthorized attempt to access admin endpoints.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Valid administrative authorization credentials required.",
        )
    return True


@router.post(
    "/revoke-tokens",
    response_model=TokenRevocationResponse,
    summary="Emergency administrative token revocation endpoint",
)
async def revoke_tokens(
    req: TokenRevocationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[bool, Depends(verify_admin_key)],
) -> TokenRevocationResponse:
    """Emergency revocation of active sessions and refresh tokens per security.md §17.3."""
    auth_repo = RefreshTokenRepository(db)
    revoked_count = 0

    if req.all_users:
        logger.critical(
            "GLOBAL TOKEN REVOCATION TRIGGERED by admin. Reason: %s", req.reason
        )
        revoked_count = await auth_repo.revoke_all_globally()
        AUTH_REFRESH_TOKEN_REUSE_TOTAL.inc()
        await db.commit()
        return TokenRevocationResponse(
            tokens_revoked_count=revoked_count,
            all_users=True,
            message=f"All active user sessions globally revoked ({revoked_count} tokens). Reason: {req.reason}",
        )

    if req.user_id:
        logger.warning(
            "Targeted user token revocation for user_id=%s. Reason: %s",
            req.user_id,
            req.reason,
        )
        revoked_count = await auth_repo.revoke_all_for_user(req.user_id)
        await db.commit()
        return TokenRevocationResponse(
            tokens_revoked_count=revoked_count,
            user_id=req.user_id,
            all_users=False,
            message=f"Revoked all sessions for user {req.user_id} ({revoked_count} tokens). Reason: {req.reason}",
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Must specify either user_id or all_users=true for token revocation.",
    )
