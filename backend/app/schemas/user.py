"""Pydantic request and response schemas for user profiles and data rights."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class UserResponse(BaseModel):
    """Sanitized public user profile representation."""

    id: uuid.UUID
    name: str
    email: str
    monthly_income: Decimal | None = None
    consent_ai: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class UserUpdateRequest(BaseModel):
    """User profile update request with strict mass-assignment prevention."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    monthly_income: Decimal | None = Field(
        default=None, ge=Decimal("0.00"), le=Decimal("10000000.00")
    )
    consent_ai: bool | None = Field(default=None)

    model_config = ConfigDict(extra="forbid")


class UserDeleteRequest(BaseModel):
    """Account erasure confirmation request."""

    password: str = Field(..., min_length=1, max_length=128)
    confirm: bool = Field(..., description="Must explicitly confirm account termination")

    model_config = ConfigDict(extra="forbid")


class UserDataExportResponse(BaseModel):
    """Comprehensive user data export payload per GDPR/Privacy standards."""

    user: UserResponse
    exported_at: datetime
    summary: dict[str, Any]
    disclaimer: str = (
        "This export contains your personal financial profile and records stored by Sohoj. "
        "Store this document securely."
    )
