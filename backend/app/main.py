"""FastAPI application factory and main entrypoint."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.router import api_router
from app.ai.safety.circuit_breaker import DailyTokenBudgetExceededError
from app.ai.safety.consent_gate import ConsentRequiredError
from app.core.config import get_settings
from app.core.errors import (
    InsufficientDataError,
    consent_required_exception_handler,
    http_exception_handler,
    insufficient_data_exception_handler,
    token_budget_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.logging import setup_logging
from app.core.metrics import prometheus_metrics_middleware
from app.core.middleware import (
    GlobalRateLimiterMiddleware,
    RequestCorrelationMiddleware,
    RequestSizeLimitMiddleware,
    SecurityHeadersMiddleware,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle management."""
    settings = get_settings()
    setup_logging(log_level="DEBUG" if settings.debug else "INFO")
    logger.info("Starting %s in %s mode", settings.app_name, settings.environment)
    yield
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    """Application factory for FastAPI."""
    settings = get_settings()

    # Disable automatic interactive docs in production per security.md §16
    docs_url = "/docs" if settings.environment != "production" else None
    redoc_url = "/redoc" if settings.environment != "production" else None
    openapi_url = "/openapi.json" if settings.environment != "production" else None

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
        lifespan=lifespan,
    )

    # 1. Register Custom Middlewares (LIFO order: outermost added last)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestSizeLimitMiddleware, max_size=settings.max_request_body_size)
    app.add_middleware(
        GlobalRateLimiterMiddleware, max_requests=settings.rate_limit_per_minute_general
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestCorrelationMiddleware)
    app.middleware("http")(prometheus_metrics_middleware)

    # 3. Register RFC 7807 Error Handlers
    app.add_exception_handler(ConsentRequiredError, consent_required_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(DailyTokenBudgetExceededError, token_budget_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(InsufficientDataError, insufficient_data_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # 4. Root Operations Endpoints (/health, /ready, /metrics)
    app.include_router(health_router)

    @app.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        """Prometheus metrics endpoint (internal access)."""
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    # 5. API V1 Routers
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
