"""Seed script to populate sohoj_demo.db with realistic synthetic demo user data."""

from __future__ import annotations

import asyncio
import os
import sys
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from enum import StrEnum

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import delete, select
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

# MFS providers supported in Sohoj
class MFSProvider(StrEnum):
    BKASH = "BKASH"
    NAGAD = "NAGAD"
    ROCKET = "ROCKET"
    UPAY = "UPAY"

MFS_PROVIDERS = {p.value for p in MFSProvider}

DATABASE_URL = "sqlite+aiosqlite:///sohoj_demo.db"


async def seed_user_dataset(
    session: AsyncSession,
    user_id: uuid.UUID,
    name: str,
    email: str,
    monthly_income: Decimal,
    persona_type: str,
    months_data: list[tuple],
    txns_data: list[tuple],
    goals_data: list[tuple],
    anomaly_data: dict,
    behavior_factors: list[dict],
    recommendation_data: dict,
) -> None:
    """Idempotently seed a complete user portfolio into the demo database."""
    # Delete previous related records for clean update
    await session.execute(delete(AIRecommendation).where(AIRecommendation.user_id == user_id))
    await session.execute(delete(BehaviorProfile).where(BehaviorProfile.user_id == user_id))
    await session.execute(delete(Anomaly).where(Anomaly.user_id == user_id))
    await session.execute(delete(Transaction).where(Transaction.user_id == user_id))
    await session.execute(delete(FinancialGoal).where(FinancialGoal.user_id == user_id))
    await session.execute(delete(MonthlyFeature).where(MonthlyFeature.user_id == user_id))

    # 1. User
    existing_user = await session.get(User, user_id)
    if existing_user:
        existing_user.name = name
        existing_user.email = email
        existing_user.monthly_income = monthly_income
        existing_user.consent_ai = True
        existing_user.updated_at = datetime.now(UTC)
    else:
        user = User(
            id=user_id,
            name=name,
            email=email,
            password_hash=hash_password("SecurePassword123!"),
            monthly_income=monthly_income,
            consent_ai=True,
            created_at=datetime.now(UTC) - timedelta(days=180),
            updated_at=datetime.now(UTC),
        )
        session.add(user)

    # 2. Monthly Features (6 months)
    for m_str, inc, exp, sav, rate, nec, disc, count, cat_breakdown in months_data:
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
            cashout_count=max(2, count // 4),
            avg_txn=Decimal(str(round(float((inc + exp) / count), 2))),
            median_txn=Decimal(str(round(float(exp / count), 2))),
            category_breakdown=cat_breakdown,
            computed_at=datetime.now(UTC),
        )
        session.add(mf)

    # 3. Transactions
    for ts, amt, t_type, purp, cat, merch, provider, desc in txns_data:
        t = Transaction(
            id=uuid.uuid4(),
            user_id=user_id,
            ts=datetime.fromisoformat(ts.replace("Z", "+00:00")),
            amount=amt,
            transaction_type=t_type,
            purpose=purp,
            category=cat,
            merchant=merch,
            mfs_provider=provider,
            description=desc,
            created_at=datetime.now(UTC),
        )
        session.add(t)

    # 4. Goals
    for g_name, target, current, target_d in goals_data:
        g = FinancialGoal(
            id=uuid.uuid4(),
            user_id=user_id,
            name=g_name,
            target_amount=target,
            current_amount=current,
            target_date=target_d,
            status="active",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        session.add(g)

    # 5. Anomaly
    anom = Anomaly(
        id=uuid.uuid4(),
        user_id=user_id,
        scope=anomaly_data.get("scope", "category_month"),
        category=anomaly_data.get("category", "electronics"),
        anomaly_score=anomaly_data.get("score", Decimal("0.8900")),
        observed_value=anomaly_data.get("observed", Decimal("12500.00")),
        baseline_value=anomaly_data.get("baseline", Decimal("3500.00")),
        deviation_pct=anomaly_data.get("deviation", Decimal("2.57")),
        explanation=anomaly_data.get("explanation", {}),
        model_version="anomaly-v1.0",
        status="open",
        created_at=datetime.now(UTC),
    )
    session.add(anom)

    # 6. Behavior Profile
    bp = BehaviorProfile(
        user_id=user_id,
        profile=persona_type,
        confidence=Decimal("0.8800"),
        model_version="behavior-v1.0",
        top_factors=behavior_factors,
        as_of_month=date(2026, 10, 1),
        created_at=datetime.now(UTC),
    )
    session.add(bp)

    # 7. AI Recommendation
    rec = AIRecommendation(
        id=uuid.uuid4(),
        user_id=user_id,
        title=recommendation_data.get("title", "Cash-Out Optimization"),
        content=recommendation_data.get("content", ""),
        type=recommendation_data.get("type", "cashout_reduction"),
        priority=1,
        source_refs={"anomaly_id": str(anom.id), "provider": "upay"},
        created_at=datetime.now(UTC),
    )
    session.add(rec)


async def seed() -> None:
    engine = create_async_engine(DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        # ---------------------------------------------------------------------
        # CLEANUP: Remove Kamrul (3rd persona) if present from previous seeds
        # ---------------------------------------------------------------------
        kamrul_id = uuid.UUID("8d6ed34b-12ac-2c7b-7b64-b69cccba9263")
        existing_kamrul = await session.get(User, kamrul_id)
        if existing_kamrul:
            await session.execute(delete(AIRecommendation).where(AIRecommendation.user_id == kamrul_id))
            await session.execute(delete(BehaviorProfile).where(BehaviorProfile.user_id == kamrul_id))
            await session.execute(delete(Anomaly).where(Anomaly.user_id == kamrul_id))
            await session.execute(delete(Transaction).where(Transaction.user_id == kamrul_id))
            await session.execute(delete(FinancialGoal).where(FinancialGoal.user_id == kamrul_id))
            await session.execute(delete(MonthlyFeature).where(MonthlyFeature.user_id == kamrul_id))
            await session.execute(delete(User).where(User.id == kamrul_id))
            print("Removed Kamrul (3rd persona) from database.")

        # ---------------------------------------------------------------------
        # PERSONA 1: Sumaiya Talukder (Ride Share Driver)
        # ---------------------------------------------------------------------
        sumaiya_id = uuid.UUID("26dafe10-4e28-744e-c919-4a0abefaa0a6")
        sumaiya_months = [
            ("2026-05-01", Decimal("34000.00"), Decimal("26000.00"), Decimal("8000.00"), Decimal("0.2353"), Decimal("18500.00"), Decimal("7500.00"), 28, {"groceries": 8325.0, "rent": 6475.0, "transportation": 3700.0, "dining_out": 3750.0, "shopping": 3750.0}),
            ("2026-06-01", Decimal("36500.00"), Decimal("27200.00"), Decimal("9300.00"), Decimal("0.2548"), Decimal("19000.00"), Decimal("8200.00"), 32, {"groceries": 8550.0, "rent": 6650.0, "transportation": 3800.0, "dining_out": 4100.0, "shopping": 4100.0}),
            ("2026-07-01", Decimal("33800.00"), Decimal("25900.00"), Decimal("7900.00"), Decimal("0.2337"), Decimal("18200.00"), Decimal("7700.00"), 30, {"groceries": 8190.0, "rent": 6370.0, "transportation": 3640.0, "dining_out": 3850.0, "shopping": 3850.0}),
            ("2026-08-01", Decimal("35500.00"), Decimal("28100.00"), Decimal("7400.00"), Decimal("0.2085"), Decimal("19500.00"), Decimal("8600.00"), 35, {"groceries": 8775.0, "rent": 6825.0, "transportation": 3900.0, "dining_out": 4300.0, "shopping": 4300.0}),
            ("2026-09-01", Decimal("37000.00"), Decimal("27800.00"), Decimal("9200.00"), Decimal("0.2486"), Decimal("19200.00"), Decimal("8600.00"), 33, {"groceries": 8640.0, "rent": 6720.0, "transportation": 3840.0, "dining_out": 4300.0, "shopping": 4300.0}),
            ("2026-10-01", Decimal("38500.00"), Decimal("28400.00"), Decimal("10100.00"), Decimal("0.2623"), Decimal("19800.00"), Decimal("8600.00"), 26, {"groceries": 8910.0, "rent": 6930.0, "transportation": 3960.0, "dining_out": 4300.0, "shopping": 4300.0}),
        ]
        sumaiya_txns = [
            ("2026-10-01T09:30:00Z", Decimal("15000.00"), "cash_in", "necessity", "salary_deposit", "bKash Payout", "bkash", "Ride Share Weekly Payout"),
            ("2026-10-02T11:15:00Z", Decimal("10000.00"), "cash_out", "necessity", "rent", "bKash Agent", "bkash", "House Rent Cash-Out"),
            ("2026-10-03T14:20:00Z", Decimal("3200.00"), "expense", "necessity", "groceries", "Shwapno", "bkash", "Shwapno Super Shop"),
            ("2026-10-04T17:45:00Z", Decimal("1450.00"), "expense", "necessity", "utilities", "Upay BillPay - DESCO", "upay", "DESCO Electricity Bill via Upay"),
            ("2026-10-05T19:10:00Z", Decimal("2500.00"), "cash_out", "necessity", "transportation", "Nagad Agent", "nagad", "Octane Fuel for Bike"),
            ("2026-10-06T12:00:00Z", Decimal("12000.00"), "cash_in", "necessity", "salary_deposit", "bKash Payout", "bkash", "Ride Share Mid-Week Payout"),
            ("2026-10-07T15:30:00Z", Decimal("1500.00"), "expense", "discretionary", "dining_out", "Cafe Rio", "bkash", "Cafe Dining with Friends"),
            ("2026-10-08T18:00:00Z", Decimal("3000.00"), "transfer", "other", "family_support", "Nagad Personal", "nagad", "Sent to Mother in Bogura"),
            ("2026-10-09T10:15:00Z", Decimal("800.00"), "expense", "necessity", "healthcare", "Lazz Pharma", "bkash", "Medicine at Lazz Pharma"),
            ("2026-10-10T16:40:00Z", Decimal("2200.00"), "expense", "discretionary", "shopping", "Aarong", "bkash", "Aarong Online"),
            ("2026-10-11T20:05:00Z", Decimal("500.00"), "expense", "necessity", "utilities", "Grameenphone", "bkash", "Grameenphone Mobile Recharge"),
            ("2026-10-12T13:25:00Z", Decimal("8500.00"), "cash_in", "necessity", "salary_deposit", "Upay Payout", "upay", "Ride Share Upay Salary Disbursement"),
            ("2026-10-13T16:00:00Z", Decimal("5000.00"), "cash_out", "necessity", "rent", "Upay Agent", "upay", "Upay Agent Cash-Out (1.4% Tariff - à§³70 fee)"),
            ("2026-10-14T11:00:00Z", Decimal("3000.00"), "cash_in", "necessity", "salary_deposit", "bKash Payout", "bkash", "Weekend Earnings"),
        ]
        sumaiya_goals = [
            ("Emergency Buffer (3 Months)", Decimal("50000.00"), Decimal("32000.00"), date(2027, 6, 30)),
            ("New E-Bike for Ride Share", Decimal("120000.00"), Decimal("45000.00"), date(2027, 12, 31)),
            ("5-Year Family DPS", Decimal("300000.00"), Decimal("85000.00"), date(2031, 10, 1)),
        ]
        sumaiya_anomaly = {
            "scope": "category_month",
            "category": "electronics",
            "score": Decimal("0.8900"),
            "observed": Decimal("12500.00"),
            "baseline": Decimal("3500.00"),
            "deviation": Decimal("2.57"),
            "explanation": {"message": "Unusual surge in electronics equipment spending via bKash payment"},
        }
        sumaiya_factors = [
            {"factor": "cashout_ratio", "impact": "High (35% of outflow volume)"},
            {"factor": "mfs_velocity", "impact": "Frequent daily micro-transfers across bKash and Upay"},
        ]
        sumaiya_rec = {
            "title": "Cash-Out Tariff Optimization",
            "content": "Switching agent cash-outs to Upay (1.4% tariff) and paying direct QR merchants saves approximately à§³450 in charges this month.",
            "type": "cashout_reduction",
        }

        await seed_user_dataset(
            session=session,
            user_id=sumaiya_id,
            name="Sumaiya Talukder",
            email="sumaiya.talukder.26dafe@example.com",
            monthly_income=Decimal("35166.11"),
            persona_type="cash_dominant_transactor",
            months_data=sumaiya_months,
            txns_data=sumaiya_txns,
            goals_data=sumaiya_goals,
            anomaly_data=sumaiya_anomaly,
            behavior_factors=sumaiya_factors,
            recommendation_data=sumaiya_rec,
        )

        # ---------------------------------------------------------------------
        # PERSONA 2: Roksana Khan (Student)
        # ---------------------------------------------------------------------
        roksana_id = uuid.UUID("71141ca9-4b05-7397-1db0-1080a27af343")
        roksana_months = [
            ("2026-05-01", Decimal("16000.00"), Decimal("13200.00"), Decimal("2800.00"), Decimal("0.1750"), Decimal("9500.00"), Decimal("3700.00"), 20, {"groceries": 3800.0, "rent": 4000.0, "education": 1700.0, "dining_out": 2000.0, "shopping": 1700.0}),
            ("2026-06-01", Decimal("16500.00"), Decimal("13800.00"), Decimal("2700.00"), Decimal("0.1636"), Decimal("9800.00"), Decimal("4000.00"), 22, {"groceries": 3900.0, "rent": 4000.0, "education": 1900.0, "dining_out": 2200.0, "shopping": 1800.0}),
            ("2026-07-01", Decimal("15800.00"), Decimal("13100.00"), Decimal("2700.00"), Decimal("0.1709"), Decimal("9400.00"), Decimal("3700.00"), 21, {"groceries": 3700.0, "rent": 4000.0, "education": 1700.0, "dining_out": 2000.0, "shopping": 1700.0}),
            ("2026-08-01", Decimal("16800.00"), Decimal("14000.00"), Decimal("2800.00"), Decimal("0.1667"), Decimal("10000.00"), Decimal("4000.00"), 24, {"groceries": 4000.0, "rent": 4000.0, "education": 2000.0, "dining_out": 2200.0, "shopping": 1800.0}),
            ("2026-09-01", Decimal("17200.00"), Decimal("14200.00"), Decimal("3000.00"), Decimal("0.1744"), Decimal("10100.00"), Decimal("4100.00"), 23, {"groceries": 4100.0, "rent": 4000.0, "education": 2000.0, "dining_out": 2300.0, "shopping": 1800.0}),
            ("2026-10-01", Decimal("17500.00"), Decimal("14500.00"), Decimal("3000.00"), Decimal("0.1714"), Decimal("10200.00"), Decimal("4300.00"), 20, {"groceries": 4100.0, "rent": 4000.0, "education": 2100.0, "dining_out": 2400.0, "shopping": 1900.0}),
        ]
        roksana_txns = [
            ("2026-10-01T10:00:00Z", Decimal("6000.00"), "cash_in", "necessity", "freelance_income", "Upay Payroll", "upay", "Monthly Physics Tutoring Honorarium Disbursed via Upay"),
            ("2026-10-02T12:30:00Z", Decimal("10000.00"), "cash_in", "other", "family_support", "Rocket P2P", "rocket", "Monthly Allowance from Father via Rocket"),
            ("2026-10-03T14:15:00Z", Decimal("650.00"), "expense", "necessity", "utilities", "Upay Utility - WASA", "upay", "Student Hostel Water & Utility via Upay"),
            ("2026-10-04T16:00:00Z", Decimal("2000.00"), "cash_out", "necessity", "transportation", "Upay Agent", "upay", "Upay Cash-Out for Semester Commute (1.4% Tariff - à§³28 fee)"),
            ("2026-10-05T18:20:00Z", Decimal("4500.00"), "expense", "necessity", "rent", "Mess Manager", "bkash", "University Hostel Mess Dues via bKash"),
            ("2026-10-06T13:40:00Z", Decimal("1850.00"), "expense", "necessity", "education", "Nilkhet Book Market", "nagad", "Semester Textbooks via Nagad"),
            ("2026-10-08T19:30:00Z", Decimal("1200.00"), "expense", "discretionary", "dining_out", "DU TSC Cafeteria", "bkash", "Study Group Meals at TSC"),
            ("2026-10-10T11:10:00Z", Decimal("499.00"), "expense", "necessity", "utilities", "bKash Recharge - Robi", "bkash", "Monthly Mobile Data Pack Recharge"),
            ("2026-10-12T15:45:00Z", Decimal("1500.00"), "cash_in", "necessity", "freelance_income", "Upay Payroll", "upay", "Weekend Coding Lab Honorarium via Upay"),
            ("2026-10-14T17:00:00Z", Decimal("1200.00"), "expense", "discretionary", "shopping", "New Market Stationery", "bkash", "Art & Project Supplies"),
        ]
        roksana_goals = [
            ("Laptop for Work/Study", Decimal("51200.00"), Decimal("22000.00"), date(2027, 3, 31)),
            ("Semester Tuition Savings", Decimal("30000.00"), Decimal("14500.00"), date(2027, 5, 15)),
        ]
        roksana_anomaly = {
            "scope": "category_month",
            "category": "dining_out",
            "score": Decimal("0.8100"),
            "observed": Decimal("3200.00"),
            "baseline": Decimal("1500.00"),
            "deviation": Decimal("2.13"),
            "explanation": {"message": "Spike in off-campus cafe dining during midterm prep week"},
        }
        roksana_factors = [
            {"factor": "discretionary_leakage", "impact": "Moderate (dining and social treats)"},
            {"factor": "multichannel_upay", "impact": "Zero-charge hostel utility bill payments via Upay"},
        ]
        roksana_rec = {
            "title": "Student Savings & Upay Utility Benefit",
            "content": "Utilize Upay zero-charge bill payments for hostel utilities and cap dining out at à§³1,500/month to hit your Laptop goal 2 months earlier.",
            "type": "savings_boost",
        }

        await seed_user_dataset(
            session=session,
            user_id=roksana_id,
            name="Roksana Khan",
            email="roksana.khan.71141c@example.com",
            monthly_income=Decimal("16637.74"),
            persona_type="mixed_drifting",
            months_data=roksana_months,
            txns_data=roksana_txns,
            goals_data=roksana_goals,
            anomaly_data=roksana_anomaly,
            behavior_factors=roksana_factors,
            recommendation_data=roksana_rec,
        )

<<<<<<< HEAD
=======
        # ---------------------------------------------------------------------
        # PERSONA 3: Kamrul Akter (Homemaker / Remittance Recipient)
        # ---------------------------------------------------------------------
        kamrul_id = uuid.UUID("8d6ed34b-12ac-2c7b-7b64-b69cccba9263")
        kamrul_months = [
            ("2026-05-01", Decimal("58000.00"), Decimal("45500.00"), Decimal("12500.00"), Decimal("0.2155"), Decimal("34000.00"), Decimal("11500.00"), 25, {"groceries": 15300.0, "rent": 13600.0, "education": 5100.0, "dining_out": 4600.0, "shopping": 6900.0}),
            ("2026-06-01", Decimal("62000.00"), Decimal("48000.00"), Decimal("14000.00"), Decimal("0.2258"), Decimal("36000.00"), Decimal("12000.00"), 27, {"groceries": 16200.0, "rent": 14400.0, "education": 5400.0, "dining_out": 4800.0, "shopping": 7200.0}),
            ("2026-07-01", Decimal("59000.00"), Decimal("45000.00"), Decimal("14000.00"), Decimal("0.2373"), Decimal("33750.00"), Decimal("11250.00"), 24, {"groceries": 15187.0, "rent": 13500.0, "education": 5063.0, "dining_out": 4500.0, "shopping": 6750.0}),
            ("2026-08-01", Decimal("61000.00"), Decimal("47200.00"), Decimal("13800.00"), Decimal("0.2262"), Decimal("35400.00"), Decimal("11800.00"), 26, {"groceries": 15930.0, "rent": 14160.0, "education": 5310.0, "dining_out": 4720.0, "shopping": 7080.0}),
            ("2026-09-01", Decimal("60500.00"), Decimal("46800.00"), Decimal("13700.00"), Decimal("0.2264"), Decimal("35100.00"), Decimal("11700.00"), 25, {"groceries": 15795.0, "rent": 14040.0, "education": 5265.0, "dining_out": 4680.0, "shopping": 7020.0}),
            ("2026-10-01", Decimal("63000.00"), Decimal("48500.00"), Decimal("14500.00"), Decimal("0.2302"), Decimal("36375.00"), Decimal("12125.00"), 22, {"groceries": 16368.0, "rent": 14550.0, "education": 5457.0, "dining_out": 4850.0, "shopping": 7275.0}),
        ]
        kamrul_txns = [
            ("2026-10-01T08:45:00Z", Decimal("45000.00"), "cash_in", "necessity", "remittance_received", "Upay Remittance", "upay", "Expatriate Remittance Disbursed directly via Upay"),
            ("2026-10-02T10:30:00Z", Decimal("18000.00"), "cash_out", "necessity", "rent", "bKash Agent", "bkash", "Family Flat Rent Cash-Out"),
            ("2026-10-03T12:00:00Z", Decimal("2850.00"), "expense", "necessity", "utilities", "Upay BillPay - NESCO", "upay", "NESCO Electricity Bill via Upay"),
            ("2026-10-04T15:00:00Z", Decimal("10000.00"), "cash_out", "necessity", "groceries", "Upay Agent", "upay", "Monthly Bazaar Raw Market Cash-Out via Upay Agent (1.4% Tariff - ৳140 fee)"),
            ("2026-10-05T17:15:00Z", Decimal("5000.00"), "expense", "savings_goal", "dps_deposit", "Dutch-Bangla Bank DPS", "rocket", "Monthly Family Shariah DPS Installment via Rocket"),
            ("2026-10-06T11:20:00Z", Decimal("6500.00"), "expense", "necessity", "education", "Ideal School & College", "nagad", "Children School Term Tuition via Nagad"),
            ("2026-10-08T14:40:00Z", Decimal("3400.00"), "expense", "necessity", "healthcare", "Tamanna Pharmacy", "bkash", "Family Health Check & Medication"),
            ("2026-10-10T09:15:00Z", Decimal("15000.00"), "cash_in", "necessity", "remittance_received", "Upay Remittance", "upay", "Secondary Family Support Remittance via Upay"),
            ("2026-10-12T16:50:00Z", Decimal("4200.00"), "expense", "discretionary", "shopping", "Apex Footwear Outlet", "bkash", "Children Winter Shoes at Apex"),
            ("2026-10-13T19:00:00Z", Decimal("950.00"), "expense", "necessity", "utilities", "Titas Gas Bill", "bkash", "Residential Piped Gas Bill via bKash"),
        ]
        kamrul_goals = [
            ("Semester Tuition Savings", Decimal("109400.00"), Decimal("65000.00"), date(2027, 4, 25)),
            ("Family Emergency Reserve", Decimal("150000.00"), Decimal("80000.00"), date(2027, 11, 30)),
            ("10-Year Shariah DPS", Decimal("500000.00"), Decimal("160000.00"), date(2036, 1, 1)),
        ]
        kamrul_anomaly = {
            "scope": "category_month",
            "category": "healthcare",
            "score": Decimal("0.8500"),
            "observed": Decimal("6800.00"),
            "baseline": Decimal("2500.00"),
            "deviation": Decimal("1.72"),
            "explanation": {"message": "Higher family healthcare and specialist physician consultation costs"},
        }
        kamrul_factors = [
            {"factor": "structured_remittance", "impact": "High (predictable monthly remittance inflows)"},
            {"factor": "upay_fee_efficiency", "impact": "Saving ৳45 per ৳10,000 cash-out using Upay's 1.4% tariff"},
        ]
        kamrul_rec = {
            "title": "Remittance Retention & Tariff Efficiency",
            "content": "Receiving remittance via Upay and taking advantage of the 1.4% tariff saves up to ৳650 in withdrawal fees compared to standard 1.85% MFS channels.",
            "type": "cashout_reduction",
        }

        await seed_user_dataset(
            session=session,
            user_id=kamrul_id,
            name="Kamrul Akter",
            email="kamrul.akter.8d6ed3@example.com",
            monthly_income=Decimal("60272.91"),
            persona_type="tight_budgeter",
            months_data=kamrul_months,
            txns_data=kamrul_txns,
            goals_data=kamrul_goals,
            anomaly_data=kamrul_anomaly,
            behavior_factors=kamrul_factors,
            recommendation_data=kamrul_rec,
        )

>>>>>>> 403f1465fb12a87eb6b261ec98469af2e03dd5ba
        await session.commit()
        print("Successfully seeded 2 demo users (Sumaiya, Roksana) with Upay transactions into sohoj_demo.db!")


if __name__ == "__main__":
    asyncio.run(seed())

