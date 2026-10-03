"""Unit tests verifying SQLAlchemy models, column types, and constraints."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Numeric, UniqueConstraint

from app.models.anomaly import Anomaly
from app.models.audit import AuditLog
from app.models.auth import RefreshToken
from app.models.behavior import BehaviorProfile
from app.models.chat import ChatMessage, Conversation
from app.models.feature import MonthlyFeature
from app.models.goal import FinancialGoal, GoalContribution
from app.models.outbox import OutboxEvent
from app.models.prediction import Prediction
from app.models.rag import RAGChunk
from app.models.recommendation import AIRecommendation
from app.models.synthetic_truth import (
    SyntheticTransactionGroundTruth,
    SyntheticUserGroundTruth,
)
from app.models.transaction import Transaction
from app.models.user import User


def test_all_models_have_tables() -> None:
    """Verify that all 17 models are properly mapped to distinct tables."""
    models = [
        User,
        Transaction,
        FinancialGoal,
        GoalContribution,
        MonthlyFeature,
        BehaviorProfile,
        Anomaly,
        Prediction,
        AIRecommendation,
        Conversation,
        ChatMessage,
        AuditLog,
        OutboxEvent,
        RAGChunk,
        SyntheticUserGroundTruth,
        SyntheticTransactionGroundTruth,
        RefreshToken,
    ]
    table_names = [m.__tablename__ for m in models]
    assert len(table_names) == 17
    assert len(table_names) == len(set(table_names)), "Table names must be unique"


def test_money_columns_are_numeric_14_2() -> None:
    """Verify that all currency/money columns use NUMERIC(14,2)."""
    assert isinstance(User.__table__.c.monthly_income.type, Numeric)
    assert User.__table__.c.monthly_income.type.precision == 14
    assert User.__table__.c.monthly_income.type.scale == 2

    assert isinstance(Transaction.__table__.c.amount.type, Numeric)
    assert Transaction.__table__.c.amount.type.precision == 14
    assert Transaction.__table__.c.amount.type.scale == 2

    assert isinstance(FinancialGoal.__table__.c.target_amount.type, Numeric)
    assert FinancialGoal.__table__.c.target_amount.type.precision == 14
    assert FinancialGoal.__table__.c.target_amount.type.scale == 2

    assert isinstance(GoalContribution.__table__.c.amount.type, Numeric)
    assert GoalContribution.__table__.c.amount.type.precision == 14
    assert GoalContribution.__table__.c.amount.type.scale == 2

    assert isinstance(MonthlyFeature.__table__.c.income.type, Numeric)
    assert MonthlyFeature.__table__.c.income.type.precision == 14
    assert MonthlyFeature.__table__.c.income.type.scale == 2


def test_transaction_constraints() -> None:
    """Verify check constraints and unique constraints on the transactions table."""
    constraints = {c.name: c for c in Transaction.__table__.constraints}

    assert "chk_transaction_amount_positive" in constraints
    amount_chk = constraints["chk_transaction_amount_positive"]
    assert isinstance(amount_chk, CheckConstraint)

    assert "chk_purpose_required_for_expense_and_cashout" in constraints
    purpose_chk = constraints["chk_purpose_required_for_expense_and_cashout"]
    assert isinstance(purpose_chk, CheckConstraint)

    assert "uq_user_idempotency_key" in constraints
    uq = constraints["uq_user_idempotency_key"]
    assert isinstance(uq, UniqueConstraint)


def test_model_instantiation() -> None:
    """Verify that models can be instantiated with valid types and default values."""
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        name="Rahim Uddin",
        email="rahim@example.com",
        password_hash="argon2id_hash_placeholder",
        monthly_income=Decimal("35000.00"),
        consent_ai=True,
    )
    assert user.name == "Rahim Uddin"
    assert user.email == "rahim@example.com"
    assert user.consent_ai is True

    txn = Transaction(
        id=uuid.uuid4(),
        user_id=user_id,
        amount=Decimal("1500.00"),
        transaction_type="expense",
        purpose="necessity",
        category="groceries",
        ts=datetime.now(UTC),
    )
    assert txn.amount == Decimal("1500.00")
    assert txn.transaction_type == "expense"
    assert txn.purpose == "necessity"
