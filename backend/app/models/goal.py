"""Financial goals and contributions models."""

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.transaction import Transaction
    from app.models.user import User

GOAL_STATUS_ENUM = Enum(
    "active",
    "achieved",
    "paused",
    "cancelled",
    name="goal_status",
    create_type=False,
)


class FinancialGoal(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """User-defined savings goal."""

    __tablename__ = "financial_goals"
    __table_args__ = (
        CheckConstraint("target_amount > 0", name="chk_goal_target_amount_positive"),
        CheckConstraint("current_amount >= 0", name="chk_goal_current_amount_non_negative"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    current_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0.00"), nullable=False
    )
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(GOAL_STATUS_ENUM, default="active", nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="goals")
    transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="goal")
    contributions: Mapped[list["GoalContribution"]] = relationship(
        "GoalContribution", back_populates="goal", cascade="all, delete-orphan"
    )


class GoalContribution(Base, UUIDPrimaryKeyMixin):
    """Explicit allocation of money toward a specific financial goal."""

    __tablename__ = "goal_contributions"
    __table_args__ = (CheckConstraint("amount > 0", name="chk_contribution_amount_positive"),)

    goal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("financial_goals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
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
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    goal: Mapped["FinancialGoal"] = relationship("FinancialGoal", back_populates="contributions")
