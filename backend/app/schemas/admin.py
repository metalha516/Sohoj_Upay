"""Pydantic V2 schemas for administration and emergency security controls."""

from __future__ import annotations

import uuid
from pydantic import BaseModel, ConfigDict, Field


class TokenRevocationRequest(BaseModel):
    """Payload to trigger immediate token revocation."""

    model_config = ConfigDict(extra="forbid")

    user_id: uuid.UUID | None = None
    all_users: bool = False
    reason: str = Field(default="Administrative security intervention", max_length=255)


class TokenRevocationResponse(BaseModel):
    """Result of token revocation execution."""

    status: str = "revoked"
    tokens_revoked_count: int
    user_id: uuid.UUID | None = None
    all_users: bool = False
    message: str
