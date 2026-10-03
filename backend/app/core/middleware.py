"""Middleware for correlation IDs, security headers, request body size limits, and rate limiting."""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import get_settings
from app.core.errors import create_problem_response
from app.core.logging import request_id_ctx_var
from app.core.rate_limit import rate_limiter

logger = logging.getLogger("app.middleware")


class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    """Middleware that attaches a unique X-Request-ID and tracks latency."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        req_id = request.headers.get("X-Request-ID")
        if not req_id:
            req_id = str(uuid.uuid4())

        token = request_id_ctx_var.set(req_id)
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        finally:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            request_id_ctx_var.reset(token)

        # Inject correlation header
        response.headers["X-Request-ID"] = req_id

        # Log structured request summary
        logger.info(
            "%s %s -> %d in %sms",
            request.method,
            request.url.path,
            response.status_code,
            latency_ms,
            extra={
                "route": request.url.path,
                "status": response.status_code,
                "latency_ms": latency_ms,
                "request_id": req_id,
            },
        )

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforce OWASP / ASVS L2 hardened HTTP security headers per security.md §5."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        settings = get_settings()

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"
        response.headers["Cache-Control"] = "no-store"

        # HSTS only on HTTPS or production/staging environments
        if request.url.scheme == "https" or settings.environment == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Enforce strict upper bound on request payload size per security.md §5 (1 MB default)."""

    def __init__(self, app: object, max_size: int = 1_048_576) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length_int = int(content_length)
                if length_int > self.max_size:
                    return create_problem_response(
                        request=request,
                        status_code=413,
                        title="Payload Too Large",
                        detail=f"Request entity exceeds allowed maximum of {self.max_size} bytes.",
                        code="PAYLOAD_TOO_LARGE",
                    )
            except ValueError:
                pass

        return await call_next(request)


class GlobalRateLimiterMiddleware(BaseHTTPMiddleware):
    """Global IP-based rate limiting middleware protecting against flood attacks."""

    def __init__(self, app: object, max_requests: int = 120, window_seconds: int = 60) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Exempt health and metrics from rate limits
        if request.url.path in ("/health", "/ready", "/metrics"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"rate_limit:global:{client_ip}"

        allowed, count, retry_after = await rate_limiter.is_allowed(
            key, max_requests=self.max_requests, window_seconds=self.window_seconds
        )

        if not allowed:
            problem = create_problem_response(
                request=request,
                status_code=429,
                title="Too Many Requests",
                detail=f"Global rate limit exceeded ({count}/{self.max_requests}). Retry in {retry_after}s.",
                code="RATE_LIMIT_EXCEEDED",
            )
            problem.headers["Retry-After"] = str(retry_after)
            return problem

        return await call_next(request)
