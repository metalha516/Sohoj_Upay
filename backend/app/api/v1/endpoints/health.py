"""Health and readiness check endpoints."""

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.errors import create_problem_response

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Operations"])


@router.get("/health", summary="Liveness Probe", status_code=status.HTTP_200_OK)
async def health_check() -> dict[str, Any]:
    """Basic liveness check verifying the application process is running."""
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
        "timestamp": datetime.now(UTC).isoformat(),
        "version": "0.1.0",
    }


@router.get("/ready", summary="Readiness Probe")
async def readiness_check(request: Request) -> JSONResponse:
    """Readiness probe checking database and cache connectivity."""
    settings = get_settings()
    checks: dict[str, str] = {
        "database": "unknown",
        "redis": "unknown",
    }
    all_ready = True

    # 1. Check PostgreSQL
    try:
        import asyncpg

        # Parse connection parameters or connect directly
        conn = await asyncpg.connect(settings.database_url, timeout=2.0)
        await conn.execute("SELECT 1")
        await conn.close()
        checks["database"] = "connected"
    except Exception as exc:
        logger.warning("Readiness DB check failed: %s", str(exc))
        checks["database"] = f"unreachable: {type(exc).__name__}"
        all_ready = False

    # 2. Check Redis
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(  # type: ignore[no-untyped-call]
            settings.redis_url,
            socket_timeout=2.0,
            socket_connect_timeout=2.0,
        )
        await r.ping()
        await r.aclose()
        checks["redis"] = "connected"
    except Exception as exc:
        logger.warning("Readiness Redis check failed: %s", str(exc))
        checks["redis"] = f"unreachable: {type(exc).__name__}"
        all_ready = False

    if not all_ready:
        return create_problem_response(
            request=request,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            title="Service Unavailable",
            detail="One or more critical backing services are unreachable.",
            code="SERVICE_UNAVAILABLE",
            errors=[{"service": k, "status": v} for k, v in checks.items() if "connected" not in v],
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "ready",
            "checks": checks,
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )
