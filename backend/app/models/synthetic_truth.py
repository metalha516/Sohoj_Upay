"""Synthetic generator ground truth models."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SyntheticUserGroundTruth(Base):
    """Quarantined ground-truth parameters for synthetic users (excluded from ML features)."""

    __tablename__ = "synthetic_user_ground_truth"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    true_persona: Mapped[str] = mapped_column(String(100), nullable=False)
    true_occupation: Mapped[str] = mapped_column(String(100), nullable=False)
    baseline_income_bdt: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    target_savings_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    is_drifting: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    drift_target_persona: Mapped[str | None] = mapped_column(String(100), nullable=True)
    drift_start_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    generator_seed: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )


class SyntheticTransactionGroundTruth(Base):
    """Quarantined ground-truth anomaly tags and shocks for synthetic transactions."""

    __tablename__ = "synthetic_transaction_ground_truth"

    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    is_injected_anomaly: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    anomaly_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    anomaly_multiplier: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    life_event_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    counterfactual_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
