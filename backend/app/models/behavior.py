"""Behavior profile model."""

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin


class BehaviorProfile(Base, UUIDPrimaryKeyMixin):
    """User behavioral archetype classification result."""

    __tablename__ = "behavior_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    profile: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    top_factors: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    savings_rate: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    necessity_rate: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    discretionary_rate: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    cashout_frequency: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    spending_variance: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    as_of_month: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
