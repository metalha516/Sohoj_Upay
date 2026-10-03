"""RFC 7807 Problem Details error models and exception handlers."""

import logging
from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import request_id_ctx_var

logger = logging.getLogger(__name__)


class ProblemDetails(BaseModel):
    """RFC 7807 Problem Details standard representation."""

    type: str = Field(
        default="about:blank", description="URI reference identifying the problem type"
    )
    title: str = Field(..., description="Short, human-readable summary of the problem type")
    status: int = Field(..., description="HTTP status code")
    detail: str = Field(..., description="Human-readable explanation specific to this occurrence")
    instance: str = Field(
        ..., description="URI reference that identifies the specific occurrence of the problem"
    )
    code: str = Field(..., description="Machine-readable error code")
    request_id: str | None = Field(default=None, description="Request correlation ID")
    errors: list[dict[str, Any]] | None = Field(
        default=None, description="Detailed field-level validation errors"
    )


def create_problem_response(
    request: Request,
    status_code: int,
    title: str,
    detail: str,
    code: str,
    errors: list[dict[str, Any]] | None = None,
    problem_type: str = "about:blank",
) -> JSONResponse:
    """Build an RFC 7807 compliant JSONResponse."""
    req_id = request_id_ctx_var.get() or request.headers.get("X-Request-ID")
    problem = ProblemDetails(
        type=problem_type,
        title=title,
        status=status_code,
        detail=detail,
        instance=str(request.url.path),
        code=code,
        request_id=req_id,
        errors=errors,
    )
    return JSONResponse(
        status_code=status_code,
        content=problem.model_dump(exclude_none=True),
        media_type="application/problem+json",
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle standard HTTP exceptions with RFC 7807 formatting."""
    title_map = {
        status.HTTP_400_BAD_REQUEST: "Bad Request",
        status.HTTP_401_UNAUTHORIZED: "Unauthorized",
        status.HTTP_403_FORBIDDEN: "Forbidden",
        status.HTTP_404_NOT_FOUND: "Not Found",
        status.HTTP_405_METHOD_NOT_ALLOWED: "Method Not Allowed",
        status.HTTP_409_CONFLICT: "Conflict",
        status.HTTP_422_UNPROCESSABLE_ENTITY: "Unprocessable Entity",
        status.HTTP_429_TOO_MANY_REQUESTS: "Too Many Requests",
        status.HTTP_500_INTERNAL_SERVER_ERROR: "Internal Server Error",
        status.HTTP_503_SERVICE_UNAVAILABLE: "Service Unavailable",
    }
    title = title_map.get(exc.status_code, "HTTP Error")
    code = f"HTTP_{exc.status_code}"
    return create_problem_response(
        request=request,
        status_code=exc.status_code,
        title=title,
        detail=str(exc.detail),
        code=code,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic schema validation failures with RFC 7807 formatting."""
    formatted_errors = []
    for err in exc.errors():
        loc = ".".join(str(part) for part in err.get("loc", []))
        formatted_errors.append(
            {
                "field": loc,
                "message": err.get("msg", "Validation error"),
                "type": err.get("type", "value_error"),
            }
        )

    return create_problem_response(
        request=request,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        title="Validation Error",
        detail="The request payload or parameters failed schema validation.",
        code="VALIDATION_ERROR",
        errors=formatted_errors,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors without leaking stack traces or internal details."""
    logger.error("Unhandled server exception: %s", str(exc), exc_info=exc)
    return create_problem_response(
        request=request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        title="Internal Server Error",
        detail="An unexpected error occurred. The incident has been recorded.",
        code="INTERNAL_SERVER_ERROR",
    )
