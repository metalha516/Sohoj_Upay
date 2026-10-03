"""Pydantic request and response schemas for authentication workflows."""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints

PasswordStr = Annotated[str, StringConstraints(min_length=12, max_length=128)]


class RegisterRequest(BaseModel):
    """User registration request."""

    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: PasswordStr
    monthly_income: Decimal | None = Field(
        default=None, ge=Decimal("0.00"), le=Decimal("10000000.00")
    )
    consent_ai: bool = Field(default=False)

    model_config = ConfigDict(extra="forbid")


class LoginRequest(BaseModel):
    """User credential login request."""

    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)

    model_config = ConfigDict(extra="forbid")


class TokenResponse(BaseModel):
    """JWT Bearer access token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(default=900, description="Token validity in seconds (15 minutes)")


class PasswordChangeRequest(BaseModel):
    """Authenticated user password modification request."""

    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: PasswordStr

    model_config = ConfigDict(extra="forbid")


class MessageResponse(BaseModel):
    """Generic informational response payload."""

    message: str
    status: str = "ok"
