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

    # 1. Check Database (Dialect-agnostic: PostgreSQL + SQLite)
    from app.db.session import check_database_health

    db_ok = await check_database_health()
    if db_ok:
        checks["database"] = "connected"
    else:
        checks["database"] = "unreachable"
        all_ready = False

    # 2. Check Redis (gracefully falls back to in-memory cache if not strictly required)
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(  # type: ignore[no-untyped-call]
            settings.redis_url,
            socket_timeout=1.5,
            socket_connect_timeout=1.5,
        )
        await r.ping()
        await r.aclose()
        checks["redis"] = "connected"
    except Exception as exc:
        if settings.redis_required:
            logger.warning("Readiness Redis check failed (required): %s", str(exc))
            checks["redis"] = f"unreachable: {type(exc).__name__}"
            all_ready = False
        else:
            checks["redis"] = "fallback_in_memory"

    if not all_ready:
        return create_problem_response(
            request=request,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            title="Service Unavailable",
            detail="One or more critical backing services are unreachable.",
            code="SERVICE_UNAVAILABLE",
            errors=[{"service": k, "status": v} for k, v in checks.items() if v not in ("connected", "fallback_in_memory")],
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "ready",
            "checks": checks,
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )
