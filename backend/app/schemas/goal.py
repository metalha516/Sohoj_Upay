"""Pydantic V2 schemas for financial goals, contributions, and progress tracking."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class GoalStatus(StrEnum):
    """Lifecycle status of a financial goal."""

    ACTIVE = "active"
    ACHIEVED = "achieved"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class GoalCreateRequest(BaseModel):
    """Payload to create a new financial goal."""

    model_config = ConfigDict(extra="forbid")

    name: Annotated[str, Field(min_length=1, max_length=255)]
    target_amount: Annotated[Decimal, Field(gt=Decimal("0.00"), max_digits=14, decimal_places=2)]
    target_date: date | None = None
    initial_amount: Annotated[
        Decimal, Field(default=Decimal("0.00"), ge=Decimal("0.00"), max_digits=14, decimal_places=2)
    ]


class GoalUpdateRequest(BaseModel):
    """Payload to update an existing financial goal with mass-assignment prevention."""

    model_config = ConfigDict(extra="forbid")

    name: Annotated[str | None, Field(min_length=1, max_length=255)] = None
    target_amount: Annotated[
        Decimal | None, Field(gt=Decimal("0.00"), max_digits=14, decimal_places=2)
    ] = None
    target_date: date | None = None
    status: GoalStatus | None = None


class GoalContributionCreateRequest(BaseModel):
    """Payload to make an explicit contribution toward a goal."""

    model_config = ConfigDict(extra="forbid")

    amount: Annotated[Decimal, Field(gt=Decimal("0.00"), max_digits=14, decimal_places=2)]
    transaction_id: uuid.UUID | None = None


class GoalContributionResponse(BaseModel):
    """Response representing a recorded goal contribution."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    goal_id: uuid.UUID
    user_id: uuid.UUID
    transaction_id: uuid.UUID | None = None
    amount: Decimal
    created_at: datetime


class GoalResponse(BaseModel):
    """Rich financial goal response augmented with progress analytics and feasibility."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    target_amount: Decimal
    current_amount: Decimal
    target_date: date | None = None
    status: str
    progress_pct: Decimal = Decimal("0.00")
    months_remaining: int | None = None
    required_monthly_saving: Decimal = Decimal("0.00")
    is_on_track: bool = True
    eta: date | None = None
    feasibility_ratio: Decimal | None = None
    created_at: datetime
    updated_at: datetime
