"""Repository for hashed refresh token management and reuse invalidation."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import RefreshToken


class RefreshTokenRepository:
    """Manages hashed refresh token lifecycle, rotation, and reuse family revocation."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        token_hash: str,
        user_id: uuid.UUID,
        expires_at: datetime,
    ) -> RefreshToken:
        """Create a new hashed refresh token record."""
        record = RefreshToken(
            token_hash=token_hash,
            user_id=user_id,
            expires_at=expires_at,
            revoked=False,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        """Look up refresh token by SHA-256 hash."""
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke(self, token_record: RefreshToken) -> None:
        """Mark a single token record as revoked."""
        token_record.revoked = True
        await self.session.flush()

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> int:
        """Revoke all refresh tokens for a user (triggered upon reuse detection or password change)."""
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
            .values(revoked=True)
            .execution_options(synchronize_session="fetch")
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return getattr(result, "rowcount", 0)

    async def revoke_all_globally(self) -> int:
        """Revoke all active refresh tokens system-wide (emergency kill switch)."""
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.revoked.is_(False))
            .values(revoked=True)
            .execution_options(synchronize_session="fetch")
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return getattr(result, "rowcount", 0)
