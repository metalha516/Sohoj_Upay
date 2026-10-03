"""Income generation engine simulating realistic occupational income streams across 2026."""

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal

import numpy as np

from data.synthetic.generator.calendar import DhakaCalendar
from data.synthetic.generator.population import SyntheticUser


@dataclass
class RawEvent:
    event_id: uuid.UUID
    user_id: uuid.UUID
    ts: datetime
    txn_type: str  # "income", "expense", "cash_in", "cash_out", "transfer"
    category: str
    purpose: str | None
    amount: Decimal
    fee: Decimal
    description: str
    merchant: str | None
    goal_id: uuid.UUID | None = None
    is_anomaly: bool = False
    anomaly_type: str | None = None
    life_event_code: str | None = None


class IncomeGenerator:
    """Generates chronological income streams, allowances, overtime, and bonuses."""

    def __init__(self, calendar: DhakaCalendar, seed: int = 42) -> None:
        self.calendar = calendar
        self.rng = np.random.default_rng(seed)

    def _make_uuid(self) -> uuid.UUID:
        return uuid.UUID(bytes=bytes(self.rng.bytes(16)))

    def generate_user_income(self, user: SyntheticUser) -> list[RawEvent]:
        """Generate all income events across the 12 months of 2026 for a user."""
        events: list[RawEvent] = []
        occ = user.occupation
        base_income = float(user.baseline_income)

        # Mid-year raise flag (~15% probability for salaried/govt/private jobs)
        has_raise = (occ in ("government_employee", "private_sector_employee")) and (
            self.rng.random() < 0.15
        )
        raise_pct = self.rng.uniform(0.06, 0.12) if has_raise else 0.0

        for month in range(1, 13):
            # Check if raise applies from July (month 7) onwards
            monthly_base = (
                base_income * (1.0 + raise_pct) if (has_raise and month >= 7) else base_income
            )

            # -------------------------------------------------------------
            # 1. Salaried Corporate & Government
            # -------------------------------------------------------------
            if occ in ("government_employee", "private_sector_employee"):
                # Salary payday cluster: 28th to 2nd
                pay_day = int(self.rng.choice([1, 2, 3, 28, 29, 30]))
                # Occasional 1-3 day salary delay (10% chance)
                if self.rng.random() < 0.10:
                    pay_day = min(28, pay_day + int(self.rng.integers(1, 4)))

                salary_date = date(2026, month, min(28, pay_day))
                salary_hour = int(self.rng.integers(10, 16))
                salary_minute = int(self.rng.integers(0, 60))
                ts = self.calendar.make_dhaka_datetime(salary_date, salary_hour, salary_minute)

                amt = Decimal(str(round(monthly_base, 2))).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                events.append(
                    RawEvent(
                        event_id=self._make_uuid(),
                        user_id=user.user_id,
                        ts=ts,
                        txn_type="income",
                        category="salary",
                        purpose="necessity",
                        amount=amt,
                        fee=Decimal("0.00"),
                        description=f"{salary_date.strftime('%B')} Monthly Salary Credit",
                        merchant=None,
                    )
                )

            # -------------------------------------------------------------
            # 2. Garment Workers (RMG)
            # -------------------------------------------------------------
            elif occ == "garment_worker":
                # Standard garment wage disbursement between 7th and 10th
                pay_day = int(self.rng.integers(7, 11))
                salary_date = date(2026, month, pay_day)
                ts = self.calendar.make_dhaka_datetime(
                    salary_date, int(self.rng.integers(14, 18)), int(self.rng.integers(0, 60))
                )

                base_wage = monthly_base * 0.85
                amt = Decimal(str(round(base_wage, 2))).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                events.append(
                    RawEvent(
                        event_id=self._make_uuid(),
                        user_id=user.user_id,
                        ts=ts,
                        txn_type="income",
                        category="salary",
                        purpose="necessity",
                        amount=amt,
                        fee=Decimal("0.00"),
                        description=f"RMG Factory Monthly Wages ({salary_date.strftime('%b')})",
                        merchant=None,
                    )
                )

                # Overtime (OT) payment: 1-2 times a month around 20th-25th
                ot_day = int(self.rng.integers(20, 26))
                ot_date = date(2026, month, ot_day)
                ot_amt = Decimal(
                    str(round(monthly_base * float(self.rng.uniform(0.10, 0.25)), 2))
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                ot_ts = self.calendar.make_dhaka_datetime(
                    ot_date, int(self.rng.integers(18, 21)), int(self.rng.integers(0, 60))
                )
                events.append(
                    RawEvent(
                        event_id=self._make_uuid(),
                        user_id=user.user_id,
                        ts=ot_ts,
                        txn_type="income",
                        category="salary",
                        purpose="necessity",
                        amount=ot_amt,
                        fee=Decimal("0.00"),
                        description="Factory Overtime Allowance",
                        merchant=None,
                    )
                )

            # -------------------------------------------------------------
            # 3. Freelancer / Gig Worker
            # -------------------------------------------------------------
            elif occ == "freelancer_gig_worker":
                # Irregular 2 to 4 milestone credits per month
                num_milestones = int(self.rng.choice([1, 2, 3, 4], p=[0.15, 0.40, 0.35, 0.10]))
                month_variance = float(self.rng.uniform(0.55, 1.45))
                total_target = monthly_base * month_variance

                days = sorted(self.rng.choice(range(1, 29), size=num_milestones, replace=False))
                split_weights = self.rng.dirichlet(np.ones(num_milestones))

                for m_day, w in zip(days, split_weights, strict=True):
                    m_date = date(2026, month, int(m_day))
                    m_ts = self.calendar.make_dhaka_datetime(
                        m_date, int(self.rng.integers(11, 22)), int(self.rng.integers(0, 60))
                    )
                    m_amt = Decimal(str(round(total_target * float(w), 2))).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                    if m_amt > Decimal("100.00"):
                        events.append(
                            RawEvent(
                                event_id=self._make_uuid(),
                                user_id=user.user_id,
                                ts=m_ts,
                                txn_type="income",
                                category="freelance_gig",
                                purpose="necessity",
                                amount=m_amt,
                                fee=Decimal("0.00"),
                                description="Freelance Milestone Payment",
                                merchant=None,
                            )
                        )

            # -------------------------------------------------------------
            # 4. Small Business / Shopkeeper
            # -------------------------------------------------------------
            elif occ == "small_shopkeeper_merchant":
                # 12 to 20 daily customer revenue deposits per month
                num_credits = int(self.rng.integers(12, 21))
                days = sorted(self.rng.choice(range(1, 29), size=num_credits, replace=False))
                avg_credit = monthly_base / float(num_credits)

                for c_day in days:
                    c_date = date(2026, month, int(c_day))
                    c_ts = self.calendar.make_dhaka_datetime(
                        c_date, int(self.rng.integers(19, 23)), int(self.rng.integers(0, 60))
                    )
                    var = self.rng.uniform(0.60, 1.50)
                    c_amt = Decimal(str(round(avg_credit * var, 2))).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                    events.append(
                        RawEvent(
                            event_id=self._make_uuid(),
                            user_id=user.user_id,
                            ts=c_ts,
                            txn_type="income",
                            category="business_revenue",
                            purpose="necessity",
                            amount=c_amt,
                            fee=Decimal("0.00"),
                            description="Daily Store Customer Sales",
                            merchant=None,
                        )
                    )

            # -------------------------------------------------------------
            # 5. Ride-Share / Delivery Driver
            # -------------------------------------------------------------
            elif occ == "ride_share_driver":
                # Weekly earnings cash-out / wallet settlement (4-5 per month)
                days = [5, 12, 19, 26]
                avg_weekly = monthly_base / 4.0
                for d_day in days:
                    d_date = date(2026, month, d_day)
                    d_ts = self.calendar.make_dhaka_datetime(
                        d_date, int(self.rng.integers(21, 23)), int(self.rng.integers(0, 60))
                    )
                    var = self.rng.uniform(0.75, 1.30)
                    d_amt = Decimal(str(round(avg_weekly * var, 2))).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                    events.append(
                        RawEvent(
                            event_id=self._make_uuid(),
                            user_id=user.user_id,
                            ts=d_ts,
                            txn_type="income",
                            category="freelance_gig",
                            purpose="necessity",
                            amount=d_amt,
                            fee=Decimal("0.00"),
                            description="Ride-sharing Platform Weekly Earnings",
                            merchant=None,
                        )
                    )

            # -------------------------------------------------------------
            # 6. Remittance Recipient
            # -------------------------------------------------------------
            elif occ == "homemaker_remittance_recipient":
                # Inflows occur 5-8 times a year, not every month
                if self.rng.random() < 0.65:
                    r_day = int(self.rng.integers(4, 25))
                    r_date = date(2026, month, r_day)
                    r_ts = self.calendar.make_dhaka_datetime(
                        r_date, int(self.rng.integers(11, 17)), int(self.rng.integers(0, 60))
                    )
                    remit_amt = monthly_base * float(self.rng.uniform(1.2, 2.4))
                    r_amt = Decimal(str(round(remit_amt, 2))).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                    events.append(
                        RawEvent(
                            event_id=self._make_uuid(),
                            user_id=user.user_id,
                            ts=r_ts,
                            txn_type="income",
                            category="remittance_received",
                            purpose="necessity",
                            amount=r_amt,
                            fee=Decimal("0.00"),
                            description="Foreign Remittance Credit (Middle East)",
                            merchant=None,
                        )
                    )

            # -------------------------------------------------------------
            # 7. Student
            # -------------------------------------------------------------
            elif occ == "student":
                # Monthly family allowance on 1st-5th
                allowance_day = int(self.rng.integers(1, 6))
                allowance_date = date(2026, month, allowance_day)
                a_ts = self.calendar.make_dhaka_datetime(
                    allowance_date, int(self.rng.integers(10, 15)), int(self.rng.integers(0, 60))
                )
                a_amt = Decimal(str(round(monthly_base * 0.85, 2))).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                events.append(
                    RawEvent(
                        event_id=self._make_uuid(),
                        user_id=user.user_id,
                        ts=a_ts,
                        txn_type="income",
                        category="family_support_received",
                        purpose="necessity",
                        amount=a_amt,
                        fee=Decimal("0.00"),
                        description="Monthly Allowance from Parents",
                        merchant=None,
                    )
                )

                # Occasional private tutoring (tuition) honorarium (~40% chance per month)
                if self.rng.random() < 0.40:
                    t_day = int(self.rng.integers(10, 20))
                    t_date = date(2026, month, t_day)
                    t_ts = self.calendar.make_dhaka_datetime(
                        t_date, int(self.rng.integers(18, 20)), int(self.rng.integers(0, 60))
                    )
                    t_amt = Decimal(str(round(float(self.rng.uniform(3000, 6000)), 2))).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                    events.append(
                        RawEvent(
                            event_id=self._make_uuid(),
                            user_id=user.user_id,
                            ts=t_ts,
                            txn_type="income",
                            category="freelance_gig",
                            purpose="necessity",
                            amount=t_amt,
                            fee=Decimal("0.00"),
                            description="Student Private Tutoring Fee",
                            merchant=None,
                        )
                    )

        # -----------------------------------------------------------------
        # 8. Festival Bonuses (Eid-ul-Fitr & Eid-ul-Adha)
        # -----------------------------------------------------------------
        if user.has_festival_bonus:
            # Eid-ul-Fitr Bonus (Mid March 2026)
            fitr_bonus_day = int(self.rng.integers(11, 16))
            fitr_date = date(2026, 3, fitr_bonus_day)
            fitr_ts = self.calendar.make_dhaka_datetime(
                fitr_date, int(self.rng.integers(11, 16)), int(self.rng.integers(0, 60))
            )
            fitr_amt = Decimal(
                str(round(base_income * float(self.rng.uniform(0.60, 1.00)), 2))
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            events.append(
                RawEvent(
                    event_id=self._make_uuid(),
                    user_id=user.user_id,
                    ts=fitr_ts,
                    txn_type="income",
                    category="salary",
                    purpose="necessity",
                    amount=fitr_amt,
                    fee=Decimal("0.00"),
                    description="Eid-ul-Fitr Festival Bonus",
                    merchant=None,
                    life_event_code="festival_bonus_windfall",
                )
            )

            # Eid-ul-Adha Bonus (Mid May 2026)
            adha_bonus_day = int(self.rng.integers(18, 23))
            adha_date = date(2026, 5, adha_bonus_day)
            adha_ts = self.calendar.make_dhaka_datetime(
                adha_date, int(self.rng.integers(11, 16)), int(self.rng.integers(0, 60))
            )
            adha_amt = Decimal(
                str(round(base_income * float(self.rng.uniform(0.60, 1.00)), 2))
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            events.append(
                RawEvent(
                    event_id=self._make_uuid(),
                    user_id=user.user_id,
                    ts=adha_ts,
                    txn_type="income",
                    category="salary",
                    purpose="necessity",
                    amount=adha_amt,
                    fee=Decimal("0.00"),
                    description="Eid-ul-Adha Festival Bonus",
                    merchant=None,
                    life_event_code="festival_bonus_windfall",
                )
            )

        return events
