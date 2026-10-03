"""Life event simulation engine for synthetic financial lifecycles."""

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

import numpy as np

from data.synthetic.generator.calendar import DhakaCalendar
from data.synthetic.generator.income import RawEvent
from data.synthetic.generator.population import SyntheticUser


@dataclass
class UserLifeEvent:
    event_code: str
    name: str
    occurred_date: date
    impact_description: str
    bdt_amount: Decimal | None = None


class LifeEventGenerator:
    """Generates stochastic life shocks and life milestones across 2026."""

    def __init__(self, calendar: DhakaCalendar, seed: int = 42) -> None:
        self.calendar = calendar
        self.rng = np.random.default_rng(seed)

    def _make_uuid(self) -> uuid.UUID:
        return uuid.UUID(bytes=bytes(self.rng.bytes(16)))

    def generate_user_life_events(
        self, user: SyntheticUser
    ) -> tuple[list[UserLifeEvent], list[RawEvent]]:
        """Sample life events and associated shock transactions for a user."""
        life_events: list[UserLifeEvent] = []
        shock_transactions: list[RawEvent] = []
        base_income = float(user.baseline_income)

        # 1. Medical Emergency (~10% annual probability)
        if self.rng.random() < 0.10:
            m_month = int(self.rng.integers(2, 11))
            m_day = int(self.rng.integers(1, 28))
            m_date = date(2026, m_month, m_day)
            m_ts = self.calendar.make_dhaka_datetime(
                m_date, int(self.rng.integers(10, 21)), int(self.rng.integers(0, 60))
            )

            med_cost = Decimal(str(round(float(self.rng.uniform(12000, 38000)), 2))).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            # Inflow from family/loan or bank to cover emergency if required
            inflow_ts = self.calendar.make_dhaka_datetime(
                m_date, int(self.rng.integers(8, 10)), int(self.rng.integers(0, 60))
            )
            support_amt = med_cost * Decimal("0.85")
            shock_transactions.append(
                RawEvent(
                    event_id=self._make_uuid(),
                    user_id=user.user_id,
                    ts=inflow_ts,
                    txn_type="cash_in",
                    category="family_support_received",
                    purpose="necessity",
                    amount=support_amt.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                    fee=Decimal("0.00"),
                    description="Emergency Medical Assistance from Family",
                    merchant=None,
                    life_event_code="medical_emergency",
                )
            )

            # Outflow: Hospital/medical expense
            shock_transactions.append(
                RawEvent(
                    event_id=self._make_uuid(),
                    user_id=user.user_id,
                    ts=m_ts,
                    txn_type="expense",
                    category="medical",
                    purpose="necessity",
                    amount=med_cost,
                    fee=Decimal("0.00"),
                    description="Emergency Hospital Admission & Medicines",
                    merchant="Square Hospital / Lazz Pharma",
                    life_event_code="medical_emergency",
                )
            )

            life_events.append(
                UserLifeEvent(
                    event_code="medical_emergency",
                    name="Medical Emergency",
                    occurred_date=m_date,
                    impact_description=f"Unplanned medical treatment costing ৳{med_cost}",
                    bdt_amount=med_cost,
                )
            )

        # 2. Wedding Social Obligation (~15% probability, clustered in winter Nov-Feb or post-Eid)
        if self.rng.random() < 0.15:
            w_month = int(self.rng.choice([1, 2, 6, 11, 12]))
            w_day = int(self.rng.integers(5, 25))
            w_date = date(2026, w_month, w_day)
            w_ts = self.calendar.make_dhaka_datetime(
                w_date, int(self.rng.integers(16, 22)), int(self.rng.integers(0, 60))
            )

            gift_cost = Decimal(
                str(round(base_income * float(self.rng.uniform(0.25, 0.60)), 2))
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            shock_transactions.append(
                RawEvent(
                    event_id=self._make_uuid(),
                    user_id=user.user_id,
                    ts=w_ts,
                    txn_type="expense",
                    category="shopping",
                    purpose="discretionary",
                    amount=gift_cost,
                    fee=Decimal("0.00"),
                    description="Close Family Wedding Gift & Formal Clothing",
                    merchant="Aarong / New Market",
                    life_event_code="wedding_social_obligation",
                )
            )

            life_events.append(
                UserLifeEvent(
                    event_code="wedding_social_obligation",
                    name="Wedding Social Obligation",
                    occurred_date=w_date,
                    impact_description=f"Wedding gift & attendance expense of ৳{gift_cost}",
                    bdt_amount=gift_cost,
                )
            )

        return life_events, shock_transactions
