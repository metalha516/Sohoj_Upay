"""Database engine and asynchronous session management.

Supports PostgreSQL Row-Level Security (RLS) via request-scoped session context.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Return singleton AsyncEngine instance."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            pool_pre_ping=True,
            future=True,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return singleton async_sessionmaker instance."""
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


async def set_session_rls_user(session: AsyncSession, user_id: uuid.UUID | str) -> None:
    """Execute SET LOCAL app.user_id to enforce PostgreSQL Row-Level Security (RLS)."""
    bind = session.bind
    if bind and "sqlite" in bind.dialect.name:
        return
    await session.execute(
        text("SET LOCAL app.user_id = :user_id"),
        {"user_id": str(user_id)},
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields a request-scoped database session."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
