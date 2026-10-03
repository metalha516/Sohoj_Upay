"""Append-only audit log repository."""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


class AuditLogRepository:
    """Repository enforcing append-only audit logging."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log_event(
        self,
        actor: str,
        action: str,
        user_id: uuid.UUID | None = None,
        resource: str | None = None,
        ip: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Append an immutable audit entry."""
        entry = AuditLog(
            actor=actor,
            action=action,
            user_id=user_id,
            resource=resource,
            ip=ip,
            metadata_=metadata,
        )
        self.session.add(entry)
        await self.session.flush()
        return entry
