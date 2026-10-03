"""Pydantic V2 schemas for financial anomalies and analyst feedback."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class AnomalyResponse(BaseModel):
    """Detected anomaly output contract."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    transaction_id: uuid.UUID | None = None
    scope: str = Field(..., description="'transaction' or 'category_month'")
    category: str | None = None
    anomaly_score: Decimal = Field(..., description="Anomaly score [0.0 - 1.0]")
    confidence: Decimal = Field(..., description="Detection confidence score")
    observed_value: Decimal
    baseline_value: Decimal
    deviation_pct: Decimal
    explanation: dict[str, Any]
    model_version: str
    status: str = Field(..., description="'open', 'dismissed', or 'confirmed'")
    created_at: datetime


class AnomalyStatusUpdateRequest(BaseModel):
    """Payload to update feedback on a detected anomaly."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["dismissed", "confirmed"] = Field(
        ..., description="Updated feedback status for the anomaly"
    )
