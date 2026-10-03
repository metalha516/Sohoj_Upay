"""Base repository with ownership-filtered queries and session context."""

import uuid
from collections.abc import Sequence
from typing import Any, cast

from sqlalchemy import Select, delete, select, text
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base


class BaseRepository[T: Base]:
    """Generic repository providing ownership-scoped database operations."""

    def __init__(self, model_cls: type[T], session: AsyncSession) -> None:
        self.model_cls = model_cls
        self.session = session

    async def set_app_user_context(self, user_id: uuid.UUID) -> None:
        """Set the PostgreSQL app.user_id session variable for Row-Level Security (RLS)."""
        await self.session.execute(
            text("SET LOCAL app.user_id = :user_id"),
            {"user_id": str(user_id)},
        )

    def _apply_ownership_filter(self, query: Select[Any], user_id: uuid.UUID) -> Select[Any]:
        """Enforce defense-in-depth ownership filtering at the ORM query level."""
        user_col = getattr(self.model_cls, "user_id", None)
        if user_col is not None:
            return query.where(user_col == user_id)

        id_col = getattr(self.model_cls, "id", None)
        if id_col is not None and self.model_cls.__name__ == "User":
            return query.where(id_col == user_id)

        return query

    async def get_by_id_for_user(self, entity_id: uuid.UUID, user_id: uuid.UUID) -> T | None:
        """Fetch a single record ensuring it belongs strictly to the requested user."""
        id_col = getattr(self.model_cls, "id", None)
        query: Select[Any] = select(self.model_cls)
        if id_col is not None:
            query = query.where(id_col == entity_id)
        query = self._apply_ownership_filter(query, user_id)
        result = await self.session.execute(query)
        return cast(T | None, result.scalar_one_or_none())

    async def list_for_user(
        self,
        user_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[T]:
        """List records belonging strictly to the requested user."""
        query: Select[Any] = select(self.model_cls)
        query = self._apply_ownership_filter(query, user_id)
        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        return cast(Sequence[T], result.scalars().all())

    async def delete_for_user(self, entity_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a record belonging strictly to the requested user."""
        stmt = delete(self.model_cls)
        id_col = getattr(self.model_cls, "id", None)
        if id_col is not None:
            stmt = stmt.where(id_col == entity_id)
        user_col = getattr(self.model_cls, "user_id", None)
        if user_col is not None:
            stmt = stmt.where(user_col == user_id)
        result = await self.session.execute(stmt)
        if isinstance(result, CursorResult):
            return result.rowcount > 0
        rowcount = getattr(result, "rowcount", 0)
        return bool(rowcount and rowcount > 0)
