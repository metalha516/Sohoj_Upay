"""Transaction database model."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.goal import FinancialGoal
    from app.models.user import User

TXN_TYPE_ENUM = Enum(
    "income",
    "expense",
    "cash_in",
    "cash_out",
    "transfer",
    name="txn_type",
    create_type=False,
)
PURPOSE_ENUM = Enum(
    "necessity",
    "savings_goal",
    "discretionary",
    "other",
    name="purpose_t",
    create_type=False,
)


class Transaction(Base, UUIDPrimaryKeyMixin):
    """Financial transaction ledger entry."""

    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="chk_transaction_amount_positive"),
        CheckConstraint(
            "transaction_type NOT IN ('expense', 'cash_out') OR purpose IS NOT NULL",
            name="chk_purpose_required_for_expense_and_cashout",
        ),
        UniqueConstraint("user_id", "idempotency_key", name="uq_user_idempotency_key"),
        Index("idx_txn_user_ts", "user_id", "ts"),
        Index("idx_txn_user_cat_ts", "user_id", "category", "ts"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    transaction_type: Mapped[str] = mapped_column(TXN_TYPE_ENUM, nullable=False)
    purpose: Mapped[str | None] = mapped_column(PURPOSE_ENUM, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    merchant: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    goal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("financial_goals.id", ondelete="SET NULL"),
        nullable=True,
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="transactions")
    goal: Mapped[Optional["FinancialGoal"]] = relationship(
        "FinancialGoal", back_populates="transactions"
    )
