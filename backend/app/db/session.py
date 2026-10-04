"""Database engine and asynchronous session management.

Supports PostgreSQL Row-Level Security (RLS) via request-scoped session context.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

from typing import Any

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
    """Return singleton AsyncEngine instance with dialect-aware connection pooling."""
    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args: dict[str, Any] = {}
        engine_kwargs: dict[str, Any] = {
            "echo": settings.debug,
            "future": True,
        }

        if "sqlite" in settings.database_url:
            connect_args["check_same_thread"] = False
        else:
            engine_kwargs["pool_pre_ping"] = True
            engine_kwargs["pool_size"] = 10
            engine_kwargs["max_overflow"] = 10
            engine_kwargs["pool_recycle"] = 1800
            engine_kwargs["pool_timeout"] = 30.0

        _engine = create_async_engine(
            settings.database_url,
            connect_args=connect_args,
            **engine_kwargs,
        )
    return _engine


async def check_database_health() -> bool:
    """Execute lightweight connectivity probe verifying database responsiveness."""
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


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
