"""Monthly aggregated features model."""

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MonthlyFeature(Base):
    """Pre-computed monthly aggregated financial facts per user."""

    __tablename__ = "monthly_features"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    month: Mapped[date] = mapped_column(Date, primary_key=True)
    income: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    expense: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0.00"), nullable=False
    )
    savings: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0.00"), nullable=False
    )
    savings_rate: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    necessity_expense: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0.00"), nullable=False
    )
    discretionary_expense: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0.00"), nullable=False
    )
    necessity_rate: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    discretionary_rate: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    txn_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cashout_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_txn: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    median_txn: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    expense_variance: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    spending_growth: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    income_expense_ratio: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    savings_consistency: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    category_breakdown: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
