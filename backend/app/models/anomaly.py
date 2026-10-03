"""Financial anomalies model."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin


class Anomaly(Base, UUIDPrimaryKeyMixin):
    """Detected unusual transaction or category spend pattern."""

    __tablename__ = "anomalies"
    __table_args__ = (
        CheckConstraint("scope IN ('transaction', 'category_month')", name="chk_anomaly_scope"),
        CheckConstraint("status IN ('open', 'dismissed', 'confirmed')", name="chk_anomaly_status"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="SET NULL"),
        nullable=True,
    )
    scope: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    anomaly_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    observed_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    baseline_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    deviation_pct: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    explanation: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
