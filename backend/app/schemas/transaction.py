"""Pydantic V2 schemas for transactions, cash-outs, and cursor pagination."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TxnType(StrEnum):
    """Permitted transaction types per data-contract.md §1."""

    INCOME = "income"
    EXPENSE = "expense"
    CASH_IN = "cash_in"
    CASH_OUT = "cash_out"
    TRANSFER = "transfer"
    PAYMENT = "payment"
    SEND_MONEY = "send_money"


class TxnPurpose(StrEnum):
    """Permitted transaction spending purposes per data-contract.md §1."""

    NECESSITY = "necessity"
    SAVINGS_GOAL = "savings_goal"
    DISCRETIONARY = "discretionary"
    OTHER = "other"


class MFSProvider(StrEnum):
    """Permitted Mobile Financial Services (MFS) providers in Bangladesh."""

    BKASH = "bkash"
    NAGAD = "nagad"
    ROCKET = "rocket"
    UPAY = "upay"
    BANK = "bank"
    OTHER = "other"


class TransactionCreateRequest(BaseModel):
    """Payload to record a new financial transaction with strict validations."""

    model_config = ConfigDict(extra="forbid")

    amount: Annotated[Decimal, Field(gt=Decimal("0.00"), max_digits=14, decimal_places=2)]
    transaction_type: TxnType
    purpose: TxnPurpose | None = None
    category: Annotated[str | None, Field(max_length=100)] = None
    merchant: Annotated[str | None, Field(max_length=255)] = None
    mfs_provider: MFSProvider | None = None
    description: Annotated[str | None, Field(max_length=1000)] = None
    goal_id: uuid.UUID | None = None
    idempotency_key: Annotated[str | None, Field(max_length=255)] = None
    ts: datetime | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            t_type = data.get("transaction_type")
            if t_type == "payment":
                data["transaction_type"] = "expense"
            elif t_type == "send_money":
                data["transaction_type"] = "transfer"
        return data

    @model_validator(mode="after")
    def validate_purpose_required_for_expense_and_cashout(self) -> TransactionCreateRequest:
        """Enforce business rule: purpose is mandatory for expense and cash_out transactions."""
        if self.transaction_type in (TxnType.EXPENSE, TxnType.CASH_OUT, TxnType.PAYMENT) and self.purpose is None:
            raise ValueError(
                f"Purpose is required for '{self.transaction_type.value}' transactions."
            )
        if self.transaction_type == TxnType.PAYMENT:
            self.transaction_type = TxnType.EXPENSE
        elif self.transaction_type == TxnType.SEND_MONEY:
            self.transaction_type = TxnType.TRANSFER
        return self


class CashoutCreateRequest(BaseModel):
    """Dedicated payload for cash-out transactions where purpose is mandatory."""

    model_config = ConfigDict(extra="forbid")

    amount: Annotated[Decimal, Field(gt=Decimal("0.00"), max_digits=14, decimal_places=2)]
    purpose: TxnPurpose = Field(
        ..., description="Spending purpose is mandatory for MFS cash-out transactions."
    )
    category: Annotated[str | None, Field(max_length=100)] = "Cash Out"
    merchant: Annotated[str | None, Field(max_length=255)] = None
    mfs_provider: MFSProvider | None = None
    description: Annotated[str | None, Field(max_length=1000)] = None
    idempotency_key: Annotated[str | None, Field(max_length=255)] = None
    ts: datetime | None = None


class TransactionResponse(BaseModel):
    """Sanitized transaction response model."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    amount: Decimal
    transaction_type: str
    purpose: str | None = None
    category: str | None = None
    merchant: str | None = None
    mfs_provider: str | None = None
    description: str | None = None
    goal_id: uuid.UUID | None = None
    idempotency_key: str | None = None
    ts: datetime
    created_at: datetime


class TransactionCursorPage(BaseModel):
    """Cursor-paginated collection of transactions."""

    items: list[TransactionResponse]
    next_cursor: str | None = None
    has_more: bool
    total_count: int | None = None
