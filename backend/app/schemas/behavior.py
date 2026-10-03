"""Pydantic V2 schemas for behavior profiles, explainability factors, and coaching insights."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BehaviorProfileResponse(BaseModel):
    """User behavioral archetype classification output."""

    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    profile: str
    confidence: Decimal = Field(..., description="Calibrated confidence score [0.0 - 1.0]")
    top_factors: list[dict[str, Any]] | dict[str, Any] = Field(
        ..., description="Key drivers explaining the assigned profile"
    )
    savings_rate: Decimal | None = None
    necessity_rate: Decimal | None = None
    discretionary_rate: Decimal | None = None
    cashout_frequency: Decimal | None = None
    spending_variance: Decimal | None = None
    model_version: str
    as_of_month: date
    is_cold_start: bool = False
    created_at: datetime

    @property
    def archetype(self) -> str:
        return self.profile


class BehaviorInsightItem(BaseModel):
    """Grounded, non-judgmental recommendation item."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: str
    title: str
    content: str
    priority: int
    source_refs: dict[str, Any] | None = None
    created_at: datetime


class BehaviorInsightsResponse(BaseModel):
    """Aggregated behavioral profile and personalized coaching insights."""

    model_config = ConfigDict(from_attributes=True)

    profile: str
    confidence: Decimal
    model_version: str
    top_factors: list[dict[str, Any]] | dict[str, Any]
    insights: list[BehaviorInsightItem] = Field(default_factory=list)
