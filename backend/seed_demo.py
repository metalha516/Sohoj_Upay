"""Seed script to populate sohoj_demo.db with realistic synthetic demo user data."""

from __future__ import annotations

import asyncio
import os
import sys
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # register all models
from app.core.security import hash_password
from app.models.anomaly import Anomaly
from app.models.base import Base
from app.models.behavior import BehaviorProfile
from app.models.feature import MonthlyFeature
from app.models.goal import FinancialGoal
from app.models.recommendation import AIRecommendation
from app.models.transaction import Transaction
from app.models.user import User

DATABASE_URL = "sqlite+aiosqlite:///sohoj_demo.db"


async def seed() -> None:
    engine = create_async_engine(DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    user_id = uuid.UUID("26dafe10-4e28-744e-c919-4a0abefaa0a6")

    async with session_factory() as session:
        # Check if user already exists
        existing = await session.get(User, user_id)
        if existing:
            print("User already seeded in database.")
            return

        # 1. User
        user = User(
            id=user_id,
            name="Sumaiya Talukder",
            email="sumaiya.talukder.26dafe@example.com",
            password_hash=hash_password("SecurePassword123!"),
            monthly_income=Decimal("35166.11"),
            consent_ai=True,
            created_at=datetime.now(UTC) - timedelta(days=180),
            updated_at=datetime.now(UTC),
        )
        session.add(user)

        # 2. Monthly Features (6 months)
        months_data = [
            ("2026-05-01", Decimal("34000.00"), Decimal("26000.00"), Decimal("8000.00"), Decimal("0.2353"), Decimal("18500.00"), Decimal("7500.00"), 28),
            ("2026-06-01", Decimal("36500.00"), Decimal("27200.00"), Decimal("9300.00"), Decimal("0.2548"), Decimal("19000.00"), Decimal("8200.00"), 32),
            ("2026-07-01", Decimal("33800.00"), Decimal("25900.00"), Decimal("7900.00"), Decimal("0.2337"), Decimal("18200.00"), Decimal("7700.00"), 30),
            ("2026-08-01", Decimal("35500.00"), Decimal("28100.00"), Decimal("7400.00"), Decimal("0.2085"), Decimal("19500.00"), Decimal("8600.00"), 35),
            ("2026-09-01", Decimal("37000.00"), Decimal("27800.00"), Decimal("9200.00"), Decimal("0.2486"), Decimal("19200.00"), Decimal("8600.00"), 33),
            ("2026-10-01", Decimal("38500.00"), Decimal("28400.00"), Decimal("10100.00"), Decimal("0.2623"), Decimal("19800.00"), Decimal("8600.00"), 24),
        ]

        for m_str, inc, exp, sav, rate, nec, disc, count in months_data:
            mf = MonthlyFeature(
                user_id=user_id,
                month=date.fromisoformat(m_str),
                income=inc,
                expense=exp,
                savings=sav,
                savings_rate=rate,
                necessity_expense=nec,
                discretionary_expense=disc,
                necessity_rate=Decimal("0.70"),
                discretionary_rate=Decimal("0.30"),
                txn_count=count,
                cashout_count=8,
                avg_txn=Decimal("1183.33"),
                median_txn=Decimal("850.00"),
                category_breakdown={
                    "groceries": float(nec * Decimal("0.45")),
                    "rent": float(nec * Decimal("0.35")),
                    "transportation": float(nec * Decimal("0.20")),
                    "dining_out": float(disc * Decimal("0.50")),
                    "shopping": float(disc * Decimal("0.50")),
                },
                computed_at=datetime.now(UTC),
            )
            session.add(mf)

        # 3. Transactions (October 2026)
        txns = [
            ("2026-10-01T09:30:00Z", Decimal("15000.00"), "cash_in", "necessity", "salary_deposit", "bKash Payout", "Ride Share Weekly Payout"),
            ("2026-10-02T11:15:00Z", Decimal("10000.00"), "cash_out", "necessity", "rent", "bKash Agent", "House Rent Cash-Out"),
            ("2026-10-03T14:20:00Z", Decimal("3200.00"), "expense", "necessity", "groceries", "Shwapno", "Shwapno Super Shop"),
            ("2026-10-04T17:45:00Z", Decimal("1800.00"), "expense", "necessity", "utilities", "DESCO", "DESCO Prepaid Electricity"),
            ("2026-10-05T19:10:00Z", Decimal("2500.00"), "cash_out", "necessity", "transportation", "Nagad Agent", "Octane Fuel for Bike"),
            ("2026-10-06T12:00:00Z", Decimal("12000.00"), "cash_in", "necessity", "salary_deposit", "bKash Payout", "Ride Share Mid-Week Payout"),
            ("2026-10-07T15:30:00Z", Decimal("1500.00"), "expense", "discretionary", "dining_out", "Cafe Rio", "Cafe Dining with Friends"),
            ("2026-10-08T18:00:00Z", Decimal("3000.00"), "transfer", "other", "family_support", "Nagad Personal", "Sent to Mother in Bogura"),
            ("2026-10-09T10:15:00Z", Decimal("800.00"), "expense", "necessity", "healthcare", "Lazz Pharma", "Medicine at Lazz Pharma"),
            ("2026-10-10T16:40:00Z", Decimal("2200.00"), "expense", "discretionary", "shopping", "Aarong", "Aarong Online"),
            ("2026-10-11T20:05:00Z", Decimal("500.00"), "expense", "necessity", "utilities", "Grameenphone", "Grameenphone Mobile Recharge"),
            ("2026-10-12T13:25:00Z", Decimal("11500.00"), "cash_in", "necessity", "salary_deposit", "bKash Payout", "Weekend Earnings"),
        ]

        for ts, amt, t_type, purp, cat, merch, desc in txns:
            t = Transaction(
                id=uuid.uuid4(),
                user_id=user_id,
                ts=datetime.fromisoformat(ts.replace("Z", "+00:00")),
                amount=amt,
                transaction_type=t_type,
                purpose=purp,
                category=cat,
                merchant=merch,
                description=desc,
                created_at=datetime.now(UTC),
            )
            session.add(t)

        # 4. Goals
        g1 = FinancialGoal(
            id=uuid.uuid4(),
            user_id=user_id,
            name="Emergency Buffer (3 Months)",
            target_amount=Decimal("50000.00"),
            current_amount=Decimal("32000.00"),
            target_date=date(2027, 6, 30),
            status="active",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        session.add(g1)

        g2 = FinancialGoal(
            id=uuid.uuid4(),
            user_id=user_id,
            name="New E-Bike for Ride Share",
            target_amount=Decimal("120000.00"),
            current_amount=Decimal("45000.00"),
            target_date=date(2027, 12, 31),
            status="active",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        session.add(g2)

        g3 = FinancialGoal(
            id=uuid.uuid4(),
            user_id=user_id,
            name="5-Year Family DPS",
            target_amount=Decimal("300000.00"),
            current_amount=Decimal("85000.00"),
            target_date=date(2031, 10, 1),
            status="active",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        session.add(g3)

        # 5. Anomaly
        anom = Anomaly(
            id=uuid.uuid4(),
            user_id=user_id,
            scope="category_month",
            category="electronics",
            anomaly_score=Decimal("0.8900"),
            observed_value=Decimal("12500.00"),
            baseline_value=Decimal("3500.00"),
            deviation_pct=Decimal("2.57"),
            explanation={"message": "Unusual surge in electronics equipment spending via bKash payment"},
            model_version="anomaly-v1.0",
            status="open",
            created_at=datetime.now(UTC),
        )
        session.add(anom)

        # 6. Behavior Profile
        bp = BehaviorProfile(
            user_id=user_id,
            profile="cash_dominant_transactor",
            confidence=Decimal("0.8800"),
            model_version="behavior-v1.0",
            top_factors=[
                {"factor": "cashout_ratio", "impact": "High (38% of outflow volume)"},
                {"factor": "mfs_velocity", "impact": "Frequent daily micro-transfers"},
            ],
            as_of_month=date(2026, 10, 1),
            created_at=datetime.now(UTC),
        )
        session.add(bp)

        # 7. AI Recommendation
        rec = AIRecommendation(
            id=uuid.uuid4(),
            user_id=user_id,
            title="Cash-Out Optimization Nudge",
            content="Switching 3 recurring vendor payments to direct bKash merchant QR payments can save approximately ৳450 in cash-out charges this month.",
            type="cashout_reduction",
            priority=1,
            source_refs={"anomaly_id": str(anom.id), "factor": "cashout_ratio"},
            created_at=datetime.now(UTC),
        )
        session.add(rec)

        await session.commit()
        print("Successfully seeded demo user Sumaiya Talukder into sohoj_demo.db!")


if __name__ == "__main__":
    asyncio.run(seed())
