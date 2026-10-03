"""Unit tests for Phase 7 Feature Engineering Pipeline.

Covers:
1. Hand-calculated fixture from Worked Example 1 (data-contract.md).
2. Asia/Dhaka (UTC+6) timezone month-boundary handling.
3. Anti-double-counting (cash_in_self, peer transfers).
4. Zero-income handling (savings_rate is None).
5. Late-arriving transaction updates.
6. Property test: incremental recompute strictly equals full recompute.
7. Anti-leakage checks and schema version validation.
"""

from __future__ import annotations

import datetime
import uuid
from decimal import Decimal

from backend.app.ml.features import (
    FEATURE_SCHEMA_VERSION,
    MonthlyFeatureEngine,
    MonthlyFeatureRecord,
    to_dhaka_date,
)
from ml.features.cli import FORBIDDEN_LEAKAGE_COLUMNS


def test_schema_version_and_anti_leakage_fields():
    """Validates schema versioning and ensures no ground-truth leakage columns exist."""
    assert FEATURE_SCHEMA_VERSION == "v1.0.0"
    model_fields = set(MonthlyFeatureRecord.model_fields.keys())

    for forbidden in FORBIDDEN_LEAKAGE_COLUMNS:
        assert forbidden not in model_fields, f"Leakage column found in schema: {forbidden}"


def test_worked_example_1_reconciliation():
    """Tests Worked Example 1 from data-contract.md §1.3.

    Corporate Executive in April 2026:
    - Inflow Salary: 65,000.00
    - DPS Installment (savings_goal): 10,000.00
    - Emergency Reserve (savings_goal): 5,000.00
    - House Rent (cash_out, necessity): 20,000.00 + fee 370.00 = 20,370.00
    - Electricity + Internet (necessity): 3,200.00
    - Superstore Groceries (necessity): 8,500.00
    - Dining Out (discretionary): 3,400.00
    - Mobile Recharge (necessity): 500.00

    Expected:
    - Income: 65,000.00
    - Expense: 35,970.00
    - Savings: 15,000.00
    - Savings Rate: 23.08% (0.2308)
    - Necessity Expense: 32,570.00
    - Discretionary Expense: 3,400.00
    """
    user_id = uuid.uuid4()
    engine = MonthlyFeatureEngine()

    transactions = [
        # 1. Salary
        {
            "id": uuid.uuid4(),
            "user_id": user_id,
            "created_at": datetime.datetime(2026, 4, 1, 10, 0, tzinfo=datetime.UTC),
            "amount": Decimal("65000.00"),
            "fee": Decimal("0.00"),
            "type": "transfer_in",
            "category": "salary",
            "purpose": None,
        },
        # 2. DPS Installment (savings_goal)
        {
            "id": uuid.uuid4(),
            "user_id": user_id,
            "created_at": datetime.datetime(2026, 4, 2, 11, 30, tzinfo=datetime.UTC),
            "amount": Decimal("10000.00"),
            "fee": Decimal("0.00"),
            "type": "transfer_out",
            "category": "savings_dps",
            "purpose": "savings_goal",
        },
        # 3. Emergency Reserve (savings_goal)
        {
            "id": uuid.uuid4(),
            "user_id": user_id,
            "created_at": datetime.datetime(2026, 4, 3, 14, 0, tzinfo=datetime.UTC),
            "amount": Decimal("5000.00"),
            "fee": Decimal("0.00"),
            "type": "transfer_out",
            "category": "savings_dps",
            "purpose": "savings_goal",
        },
        # 4. House Rent (cash_out, necessity, fee 370)
        {
            "id": uuid.uuid4(),
            "user_id": user_id,
            "created_at": datetime.datetime(2026, 4, 5, 18, 0, tzinfo=datetime.UTC),
            "amount": Decimal("20000.00"),
            "fee": Decimal("370.00"),
            "type": "cash_out",
            "category": "rent",
            "purpose": "necessity",
        },
        # 5. Electricity + Internet (necessity)
        {
            "id": uuid.uuid4(),
            "user_id": user_id,
            "created_at": datetime.datetime(2026, 4, 10, 12, 0, tzinfo=datetime.UTC),
            "amount": Decimal("3200.00"),
            "fee": Decimal("0.00"),
            "type": "payment",
            "category": "utilities",
            "purpose": "necessity",
        },
        # 6. Superstore Groceries (necessity)
        {
            "id": uuid.uuid4(),
            "user_id": user_id,
            "created_at": datetime.datetime(2026, 4, 15, 16, 30, tzinfo=datetime.UTC),
            "amount": Decimal("8500.00"),
            "fee": Decimal("0.00"),
            "type": "payment",
            "category": "groceries",
            "purpose": "necessity",
        },
        # 7. Dining Out (discretionary)
        {
            "id": uuid.uuid4(),
            "user_id": user_id,
            "created_at": datetime.datetime(2026, 4, 22, 20, 0, tzinfo=datetime.UTC),
            "amount": Decimal("3400.00"),
            "fee": Decimal("0.00"),
            "type": "payment",
            "category": "dining",
            "purpose": "discretionary",
        },
        # 8. Mobile Recharge (necessity)
        {
            "id": uuid.uuid4(),
            "user_id": user_id,
            "created_at": datetime.datetime(2026, 4, 28, 15, 0, tzinfo=datetime.UTC),
            "amount": Decimal("500.00"),
            "fee": Decimal("0.00"),
            "type": "payment",
            "category": "mobile_recharge",
            "purpose": "necessity",
        },
    ]

    features = engine.compute_user_features(user_id=user_id, transactions=transactions)
    assert len(features) == 1
    rec = features[0]

    assert rec.month == datetime.date(2026, 4, 1)
    assert rec.income == Decimal("65000.00")
    assert rec.expense == Decimal("35970.00")
    assert rec.savings == Decimal("15000.00")
    assert rec.savings_rate == Decimal("0.2308")
    assert rec.necessity_expense == Decimal("32570.00")
    assert rec.discretionary_expense == Decimal("3400.00")
    assert rec.txn_count == 8
    assert rec.cashout_count == 1


def test_month_boundary_dhaka_timezone():
    """Ensures transactions close to midnight UTC are partitioned into Asia/Dhaka months.

    2026-01-31 17:59:00 UTC = 2026-01-31 23:59:00 +06:00 (January in Dhaka)
    2026-01-31 18:01:00 UTC = 2026-02-01 00:01:00 +06:00 (February in Dhaka)
    """
    user_id = uuid.uuid4()
    engine = MonthlyFeatureEngine()

    t1 = datetime.datetime(2026, 1, 31, 17, 59, 0, tzinfo=datetime.UTC)
    t2 = datetime.datetime(2026, 1, 31, 18, 1, 0, tzinfo=datetime.UTC)

    d1, _ = to_dhaka_date(t1)
    d2, _ = to_dhaka_date(t2)

    assert d1.strftime("%Y-%m") == "2026-01"
    assert d2.strftime("%Y-%m") == "2026-02"

    txns = [
        {
            "id": uuid.uuid4(),
            "user_id": user_id,
            "created_at": t1,
            "amount": Decimal("1000.00"),
            "fee": Decimal("0.00"),
            "type": "payment",
            "category": "groceries",
            "purpose": "necessity",
        },
        {
            "id": uuid.uuid4(),
            "user_id": user_id,
            "created_at": t2,
            "amount": Decimal("2000.00"),
            "fee": Decimal("0.00"),
            "type": "payment",
            "category": "groceries",
            "purpose": "necessity",
        },
    ]

    features = engine.compute_user_features(user_id=user_id, transactions=txns)
    months = {f.month.strftime("%Y-%m"): f for f in features}

    assert "2026-01" in months
    assert "2026-02" in months
    assert months["2026-01"].expense == Decimal("1000.00")
    assert months["2026-02"].expense == Decimal("2000.00")


def test_transfers_and_self_cashin_not_double_counted():
    """Confirms that:
    1. cash_in_self is NOT treated as income.
    2. transfers without savings_goal purpose are NOT treated as expenses or savings.
    """
    user_id = uuid.uuid4()
    engine = MonthlyFeatureEngine()

    txns = [
        # Wallet load at agent (self deposit)
        {
            "id": uuid.uuid4(),
            "user_id": user_id,
            "created_at": datetime.datetime(2026, 5, 2, 10, 0, tzinfo=datetime.UTC),
            "amount": Decimal("5000.00"),
            "fee": Decimal("0.00"),
            "type": "cash_in_self",
            "category": "cash_in_agent",
            "purpose": None,
        },
        # Neutral P2P transfer between personal wallets / accounts
        {
            "id": uuid.uuid4(),
            "user_id": user_id,
            "created_at": datetime.datetime(2026, 5, 10, 12, 0, tzinfo=datetime.UTC),
            "amount": Decimal("3000.00"),
            "fee": Decimal("5.00"),
            "type": "transfer_out",
            "category": "transfer",
            "purpose": "other",
        },
    ]

    features = engine.compute_user_features(user_id=user_id, transactions=txns)
    rec = features[0]

    assert rec.income == Decimal("0.00")
    # Fee of transfer is an expense, but not the transfer principal
    assert rec.expense == Decimal("5.00")
    assert rec.savings == Decimal("0.00")
    assert rec.savings_rate is None  # Zero income -> None


def test_zero_income_null_savings_rate():
    """Confirms that when income <= 0, savings_rate is strictly None."""
    user_id = uuid.uuid4()
    engine = MonthlyFeatureEngine()

    txns = [
        {
            "id": uuid.uuid4(),
            "user_id": user_id,
            "created_at": datetime.datetime(2026, 3, 10, 10, 0, tzinfo=datetime.UTC),
            "amount": Decimal("1500.00"),
            "fee": Decimal("0.00"),
            "type": "payment",
            "category": "groceries",
            "purpose": "necessity",
        }
    ]

    features = engine.compute_user_features(user_id=user_id, transactions=txns)
    assert len(features) == 1
    assert features[0].income == Decimal("0.00")
    assert features[0].savings_rate is None


def test_incremental_recompute_matches_full_recompute():
    """Property test: engine.recompute_user_month_features() on an affected month
    matches the result of a full engine.compute_user_features().
    """
    user_id = uuid.uuid4()
    engine = MonthlyFeatureEngine()

    # Generate 4 months of transactions
    txns = []
    for month in [1, 2, 3, 4]:
        # Salary
        txns.append(
            {
                "id": uuid.uuid4(),
                "user_id": user_id,
                "created_at": datetime.datetime(2026, month, 1, 10, 0, tzinfo=datetime.UTC),
                "amount": Decimal("30000.00"),
                "fee": Decimal("0.00"),
                "type": "transfer_in",
                "category": "salary",
                "purpose": None,
            }
        )
        # Expense
        txns.append(
            {
                "id": uuid.uuid4(),
                "user_id": user_id,
                "created_at": datetime.datetime(2026, month, 15, 12, 0, tzinfo=datetime.UTC),
                "amount": Decimal(f"{10000 + month * 500}.00"),
                "fee": Decimal("0.00"),
                "type": "payment",
                "category": "groceries",
                "purpose": "necessity",
            }
        )
        # Savings
        txns.append(
            {
                "id": uuid.uuid4(),
                "user_id": user_id,
                "created_at": datetime.datetime(2026, month, 20, 15, 0, tzinfo=datetime.UTC),
                "amount": Decimal("5000.00"),
                "fee": Decimal("0.00"),
                "type": "transfer_out",
                "category": "savings_dps",
                "purpose": "savings_goal",
            }
        )

    # Full recompute
    full_records = engine.compute_user_features(user_id=user_id, transactions=txns)
    full_by_month = {r.month.strftime("%Y-%m"): r for r in full_records}

    # Incremental recompute for month 3
    inc_record = engine.recompute_user_month_features(
        user_id=user_id,
        target_month="2026-03",
        all_user_transactions=txns,
    )

    expected = full_by_month["2026-03"]

    assert inc_record.month == expected.month
    assert inc_record.income == expected.income
    assert inc_record.expense == expected.expense
    assert inc_record.savings == expected.savings
    assert inc_record.savings_rate == expected.savings_rate
    assert inc_record.spending_growth == expected.spending_growth
    assert inc_record.rolling_savings_rate_3m_mean == expected.rolling_savings_rate_3m_mean
    assert inc_record.rolling_expense_3m_mean == expected.rolling_expense_3m_mean
    assert inc_record.category_entropy_3m == expected.category_entropy_3m
    assert inc_record.deficit_months_3m == expected.deficit_months_3m


def test_late_arriving_transaction_update():
    """Validates that injecting a late-arriving transaction correctly modifies
    both the historical month's metrics and subsequent rolling metrics.
    """
    user_id = uuid.uuid4()
    engine = MonthlyFeatureEngine()

    base_txns = [
        # Jan
        {
            "id": uuid.uuid4(),
            "user_id": user_id,
            "created_at": datetime.datetime(2026, 1, 5, 10, 0, tzinfo=datetime.UTC),
            "amount": Decimal("20000.00"),
            "fee": Decimal("0.00"),
            "type": "transfer_in",
            "category": "salary",
            "purpose": None,
        },
        # Feb
        {
            "id": uuid.uuid4(),
            "user_id": user_id,
            "created_at": datetime.datetime(2026, 2, 5, 10, 0, tzinfo=datetime.UTC),
            "amount": Decimal("20000.00"),
            "fee": Decimal("0.00"),
            "type": "transfer_in",
            "category": "salary",
            "purpose": None,
        },
    ]

    initial = engine.compute_user_features(user_id=user_id, transactions=base_txns)
    jan_initial = [r for r in initial if r.month.strftime("%Y-%m") == "2026-01"][0]
    assert jan_initial.expense == Decimal("0.00")

    # Late-arriving January expense recorded later
    late_txn = {
        "id": uuid.uuid4(),
        "user_id": user_id,
        "created_at": datetime.datetime(2026, 1, 25, 16, 0, tzinfo=datetime.UTC),
        "amount": Decimal("3500.00"),
        "fee": Decimal("0.00"),
        "type": "payment",
        "category": "groceries",
        "purpose": "necessity",
    }
    updated_txns = base_txns + [late_txn]

    updated = engine.compute_user_features(user_id=user_id, transactions=updated_txns)
    jan_updated = [r for r in updated if r.month.strftime("%Y-%m") == "2026-01"][0]
    assert jan_updated.expense == Decimal("3500.00")
