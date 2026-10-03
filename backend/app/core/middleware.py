"""Middleware for request correlation, latency tracking, and security headers."""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import request_id_ctx_var

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

        # Inject baseline HTTP security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store"

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
