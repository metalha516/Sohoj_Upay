"""Spending behavior engine implementing Engel's law, bill cycles, and Bangladeshi MFS patterns."""

import uuid
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

import numpy as np

from data.synthetic.generator.calendar import DhakaCalendar
from data.synthetic.generator.income import RawEvent
from data.synthetic.generator.population import SyntheticUser

MERCHANTS_BY_CATEGORY = {
    "groceries": [
        "Shwapno Super Shop",
        "Meena Bazar",
        "Agora Superstore",
        "Karwan Bazar Kacha Bazar",
        "Mohammadpur Krishi Market",
        "Mirpur-1 Bazar",
        "Rampura Kacha Bazar",
        "Local Mudir Dokan",
        "Bikrampur General Store",
        "Bhai Bhai Grocery",
    ],
    "dining": [
        "Takeout Burgers",
        "Sultan's Dine Kacchi",
        "Kacchi Bhai",
        "Al-Razzak Restaurant",
        "Star Kabab & Restaurant",
        "Dhanmondi Nasta Corner",
        "CP Five Star",
        "Gloria Jean's Coffees",
        "North End Coffee Roasters",
        "Local Cha-Tongi Dokan",
    ],
    "transport": [
        "Pathao Ride",
        "Uber BD Rides",
        "Shohoz Bus Booking",
        "Dhaka Chaka AC Bus",
        "Metro Rail MRT Pass",
        "Local CNG Auto-rickshaw",
        "Green Line Paribahan",
        "Hanif Enterprise",
    ],
    "utilities": [
        "DESCO Smart Prepaid Meter",
        "DPDC Electricity Bill",
        "Titas Gas Prepaid Meter",
        "Dhaka WASA Water Bill",
        "Carnival Internet BD",
        "Link3 Broadband",
        "Amber IT Fiber",
    ],
    "mobile_recharge": [
        "Grameenphone Flexiload",
        "Robi Axiata Top-up",
        "Banglalink Easy Recharge",
        "Teletalk Mobile Topup",
        "Airtel BD Top-up",
    ],
    "shopping": [
        "Aarong Flagship Outlet",
        "Yellow Lifestyle",
        "Daraz Online Shopping",
        "Bata Shoes BD",
        "Apex Footwear Outlet",
        "New Market Cloth Store",
        "Bashundhara City Complex",
    ],
    "medical": [
        "Lazz Pharma Central",
        "Bengal Pharmacy",
        "Square Hospital Pharmacy",
        "Popular Diagnostic Center",
        "Ibn Sina Medical Center",
        "Local Dispensary",
    ],
    "education": [
        "BRAC University Accounts",
        "North South University Fees",
        "Dhaka Residential Model College",
        "Viqarunnisa Noon School",
        "Mentors Coaching Center",
        "British Council IELTS",
    ],
    "family_support": [
        "Agent Send Money Cash In",
        "P2P Money Transfer to Village",
        "BKash P2P Family Support",
    ],
    "charity": [
        "Bidyanondo Foundation",
        "As-Sunnah Foundation Zakat",
        "Local Mosque Donation Committee",
        "Anjuman Mufidul Islam",
    ],
}

DESCRIPTIONS_BY_CATEGORY = {
    "groceries": [
        "Weekly bazaar groceries",
        "Bazar khoroch o mach",
        "Mudir dokan theke chul o dal",
        "Shobji o fol kinlam",
    ],
    "dining": [
        "Friends dinner",
        "Bikal er nasta o cha",
        "Office lunch",
        "Kacchi party",
        "Family restaurant dinner",
    ],
    "transport": [
        "Office jaoar rickshaw vara",
        "Pathao ride fare",
        "Metro rail fare",
        "Bus vara",
        "CNG auto ride",
    ],
    "utilities": [
        "Bidyut bill porishodh",
        "DESCO meter token recharge",
        "Wifi internet bill",
        "Gas o pani bill",
    ],
    "mobile_recharge": [
        "Mobile talktime recharge",
        "Internet pack purchase",
        "Monthly combo bundle",
        "Emergency flexiload",
    ],
    "shopping": [
        "Notun jama kapor kinlam",
        "Shoe & footwear purchase",
        "Ghorer jinishpotro",
        "Eid shopping",
    ],
    "medical": [
        "Oshudh o doctor consultation",
        "Blood test at diagnostic",
        "Prescription medicines",
    ],
    "education": ["Semester tuition payment", "Coaching fee o books", "Exam registration fee"],
    "family_support": [
        "Gramer barite taka pathalam",
        "Amma ke khoroch dilam",
        "Chotobhai er porashunar taka",
    ],
    "charity": ["Zakat payment", "Jumma namaj er por dan", "Fitra o sadaqah"],
    "rent": ["Ghorer basha bhara", "Mess er seat rent", "Monthly apartment rent"],
}


class SpendingBehaviorEngine:
    """Simulates realistic MFS expenditure transactions, bill payments, and cash-outs."""

    def __init__(self, calendar: DhakaCalendar, seed: int = 42) -> None:
        self.calendar = calendar
        self.rng = np.random.default_rng(seed)

    def _make_uuid(self) -> uuid.UUID:
        return uuid.UUID(bytes=bytes(self.rng.bytes(16)))

    def generate_user_spending(
        self, user: SyntheticUser, income_events: list[RawEvent]
    ) -> list[RawEvent]:
        """Generate spending events across all 12 months for a user."""
        events: list[RawEvent] = []
        base_income = float(user.baseline_income)
        persona = user.persona

        # User favorite merchants (simulating repetitive habits)
        fav_merchants: dict[str, str] = {}
        for cat, m_list in MERCHANTS_BY_CATEGORY.items():
            fav_merchants[cat] = str(self.rng.choice(m_list))

        # Engel's law necessity factor: lower income => higher necessity share
        # Base necessity fraction ranges from ~0.50 (high income) to ~0.88 (low income)
        engels_necessity_share = min(0.88, max(0.50, 0.88 - (base_income / 120000.0) * 0.38))

        # Persona adjustments
        if persona == "tight_budgeter":
            engels_necessity_share = min(0.92, engels_necessity_share + 0.10)
        elif persona == "discretionary_spender":
            engels_necessity_share = max(0.40, engels_necessity_share - 0.15)
        elif persona == "consistent_saver":
            engels_necessity_share = min(0.80, engels_necessity_share)

        # Monthly simulation
        for month in range(1, 13):
            # Check for drifting persona mid-year
            current_persona = persona
            if (
                user.is_drifting
                and user.drift_month
                and month >= user.drift_month
                and user.secondary_persona
            ):
                current_persona = user.secondary_persona

            # -------------------------------------------------------------
            # A. Fixed Commitments (Rent, Utilities, Internet)
            # -------------------------------------------------------------
            if user.rent_status == "renter":
                # Rent is typically 20% to 35% of monthly income, rounded to round ৳500/৳1,000
                rent_est = round(base_income * float(self.rng.uniform(0.20, 0.32)) / 500.0) * 500
                rent_bdt = Decimal(str(max(2000, rent_est))).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                rent_day = int(self.rng.integers(1, 6))
                rent_date = date(2026, month, rent_day)
                rent_ts = self.calendar.make_dhaka_datetime(
                    rent_date, int(self.rng.integers(10, 18)), int(self.rng.integers(0, 60))
                )
                events.append(
                    RawEvent(
                        event_id=self._make_uuid(),
                        user_id=user.user_id,
                        ts=rent_ts,
                        txn_type="expense",
                        category="rent",
                        purpose="necessity",
                        amount=rent_bdt,
                        fee=Decimal("0.00"),
                        description=f"{rent_date.strftime('%B')} Monthly Rent",
                        merchant=None,
                    )
                )

            # Utilities: Electricity, Gas/Water, Broadband Internet
            # Between 10th and 18th
            util_days = sorted(self.rng.choice(range(10, 19), size=2, replace=False))
            # 1. Electricity / Gas (Rounded to nearest ৳10)
            elec_amt = Decimal(str(round(float(self.rng.uniform(600, 2400)) / 10.0) * 10)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            elec_date = date(2026, month, int(util_days[0]))
            elec_ts = self.calendar.make_dhaka_datetime(
                elec_date, int(self.rng.integers(11, 16)), int(self.rng.integers(0, 60))
            )
            events.append(
                RawEvent(
                    event_id=self._make_uuid(),
                    user_id=user.user_id,
                    ts=elec_ts,
                    txn_type="expense",
                    category="utilities",
                    purpose="necessity",
                    amount=elec_amt,
                    fee=Decimal("0.00"),
                    description="Monthly Electricity Bill (DESCO/DPDC)",
                    merchant=fav_merchants["utilities"],
                )
            )

            # 2. Internet / Broadband Bill
            net_amt = Decimal(str(self.rng.choice([500, 800, 1000, 1200]))).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            net_date = date(2026, month, int(util_days[1]))
            net_ts = self.calendar.make_dhaka_datetime(
                net_date, int(self.rng.integers(14, 20)), int(self.rng.integers(0, 60))
            )
            events.append(
                RawEvent(
                    event_id=self._make_uuid(),
                    user_id=user.user_id,
                    ts=net_ts,
                    txn_type="expense",
                    category="utilities",
                    purpose="necessity",
                    amount=net_amt,
                    fee=Decimal("0.00"),
                    description="Home Fiber Broadband Internet Bill",
                    merchant=fav_merchants["utilities"],
                )
            )

            # -------------------------------------------------------------
            # B. Goal Contributions / Savings Deposits
            # -------------------------------------------------------------
            if user.goals and current_persona in ("consistent_saver", "balanced_spender"):
                for goal in user.goals:
                    if goal.status == "active":
                        # Monthly contribution between 5% and 15% of income
                        contrib_pct = (
                            self.rng.uniform(0.05, 0.14)
                            if current_persona == "consistent_saver"
                            else self.rng.uniform(0.02, 0.08)
                        )
                        contrib_amt = Decimal(str(round(base_income * contrib_pct, -1))).quantize(
                            Decimal("0.01"), rounding=ROUND_HALF_UP
                        )
                        if contrib_amt >= Decimal("200.00"):
                            c_day = int(self.rng.integers(5, 12))
                            c_date = date(2026, month, c_day)
                            c_ts = self.calendar.make_dhaka_datetime(
                                c_date,
                                int(self.rng.integers(11, 17)),
                                int(self.rng.integers(0, 60)),
                            )
                            events.append(
                                RawEvent(
                                    event_id=self._make_uuid(),
                                    user_id=user.user_id,
                                    ts=c_ts,
                                    txn_type="transfer",
                                    category="savings_deposit",
                                    purpose="savings_goal",
                                    amount=contrib_amt,
                                    fee=Decimal("0.00"),
                                    description=f"Monthly deposit to goal: {goal.title}",
                                    merchant=None,
                                    goal_id=goal.goal_id,
                                )
                            )

            # -------------------------------------------------------------
            # C. Variable Frequent Spending (Groceries, Transport, Dining, Recharge)
            # -------------------------------------------------------------
            # 1. Groceries & Bazaar (Weekly Friday/Saturday + Midweek)
            # 4-6 bazaar transactions per month
            num_groceries = int(self.rng.integers(4, 7))
            g_days = sorted(self.rng.choice(range(1, 29), size=num_groceries, replace=False))
            for g_day in g_days:
                g_date = date(2026, month, int(g_day))
                mult = self.calendar.get_category_multiplier("groceries", g_date)
                is_weekend = self.calendar.is_weekend(g_date)
                # Weekend morning bazaar basket is larger
                avg_basket = (base_income * 0.04) * (1.4 if is_weekend else 0.8) * float(mult)
                g_amt = Decimal(
                    str(round(max(250.0, avg_basket * float(self.rng.uniform(0.75, 1.35))), 2))
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                g_hour = (
                    int(self.rng.integers(7, 11)) if is_weekend else int(self.rng.integers(17, 21))
                )
                g_ts = self.calendar.make_dhaka_datetime(
                    g_date, g_hour, int(self.rng.integers(0, 60))
                )
                merchant = (
                    fav_merchants["groceries"]
                    if self.rng.random() < 0.70
                    else str(self.rng.choice(MERCHANTS_BY_CATEGORY["groceries"]))
                )
                desc = str(self.rng.choice(DESCRIPTIONS_BY_CATEGORY["groceries"]))
                events.append(
                    RawEvent(
                        event_id=self._make_uuid(),
                        user_id=user.user_id,
                        ts=g_ts,
                        txn_type="expense",
                        category="groceries",
                        purpose="necessity",
                        amount=g_amt,
                        fee=Decimal("0.00"),
                        description=desc,
                        merchant=merchant,
                    )
                )

            # 2. Daily Commute / Transport (8-16 per month)
            num_transport = int(self.rng.integers(8, 17))
            t_days = sorted(self.rng.choice(range(1, 29), size=num_transport, replace=False))
            for t_day in t_days:
                t_date = date(2026, month, int(t_day))
                # Weekdays heavier than weekends
                t_hour = (
                    int(self.rng.choice([8, 9, 17, 18, 19]))
                    if not self.calendar.is_weekend(t_date)
                    else int(self.rng.integers(14, 21))
                )
                t_ts = self.calendar.make_dhaka_datetime(
                    t_date, t_hour, int(self.rng.integers(0, 60))
                )
                t_amt = Decimal(
                    str(self.rng.choice([30, 40, 50, 70, 100, 150, 220, 350]))
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                desc = str(self.rng.choice(DESCRIPTIONS_BY_CATEGORY["transport"]))
                events.append(
                    RawEvent(
                        event_id=self._make_uuid(),
                        user_id=user.user_id,
                        ts=t_ts,
                        txn_type="expense",
                        category="transport",
                        purpose="necessity",
                        amount=t_amt,
                        fee=Decimal("0.00"),
                        description=desc,
                        merchant=fav_merchants["transport"],
                    )
                )

            # 3. Dining & Street Food (3-8 per month)
            num_dining = int(self.rng.integers(2, 8))
            if current_persona == "discretionary_spender":
                num_dining += 4
            elif current_persona == "tight_budgeter":
                num_dining = max(1, num_dining - 3)

            d_days = sorted(self.rng.choice(range(1, 29), size=min(27, num_dining), replace=False))
            for d_day in d_days:
                d_date = date(2026, month, int(d_day))
                d_mult = self.calendar.get_category_multiplier("dining", d_date)
                d_hour = int(self.rng.integers(18, 23))  # Evening dinner / adda
                d_ts = self.calendar.make_dhaka_datetime(
                    d_date, d_hour, int(self.rng.integers(0, 60))
                )
                d_amt = Decimal(
                    str(round(float(self.rng.uniform(150, 950)) * float(d_mult), 2))
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                desc = str(self.rng.choice(DESCRIPTIONS_BY_CATEGORY["dining"]))
                merchant = (
                    fav_merchants["dining"]
                    if self.rng.random() < 0.60
                    else str(self.rng.choice(MERCHANTS_BY_CATEGORY["dining"]))
                )
                events.append(
                    RawEvent(
                        event_id=self._make_uuid(),
                        user_id=user.user_id,
                        ts=d_ts,
                        txn_type="expense",
                        category="dining",
                        purpose="discretionary",
                        amount=d_amt,
                        fee=Decimal("0.00"),
                        description=desc,
                        merchant=merchant,
                    )
                )

            # 4. Mobile Recharge (3-7 per month, small realistic denominations)
            num_recharges = int(self.rng.integers(3, 8))
            r_days = sorted(self.rng.choice(range(1, 29), size=num_recharges, replace=False))
            recharge_denoms = [20, 29, 39, 49, 99, 109, 149, 199, 298, 498]
            for r_day in r_days:
                r_date = date(2026, month, int(r_day))
                r_ts = self.calendar.make_dhaka_datetime(
                    r_date, int(self.rng.integers(9, 22)), int(self.rng.integers(0, 60))
                )
                r_amt = Decimal(str(self.rng.choice(recharge_denoms))).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                desc = str(self.rng.choice(DESCRIPTIONS_BY_CATEGORY["mobile_recharge"]))
                events.append(
                    RawEvent(
                        event_id=self._make_uuid(),
                        user_id=user.user_id,
                        ts=r_ts,
                        txn_type="expense",
                        category="mobile_recharge",
                        purpose="necessity",
                        amount=r_amt,
                        fee=Decimal("0.00"),
                        description=desc,
                        merchant=fav_merchants["mobile_recharge"],
                    )
                )

            # 5. Seasonal Festivals: Eid-ul-Fitr Shopping (March), Eid-ul-Adha Qurbani (May), Pohela Boishakh (April)
            if month == 3:  # March: Pre-Eid-ul-Fitr shopping
                num_shop = int(self.rng.integers(2, 5))
                shop_days = sorted(self.rng.choice(range(5, 19), size=num_shop, replace=False))
                for s_day in shop_days:
                    s_date = date(2026, 3, int(s_day))
                    s_ts = self.calendar.make_dhaka_datetime(
                        s_date, int(self.rng.integers(15, 21)), int(self.rng.integers(0, 60))
                    )
                    s_amt = Decimal(
                        str(round(base_income * float(self.rng.uniform(0.08, 0.22)), 2))
                    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    events.append(
                        RawEvent(
                            event_id=self._make_uuid(),
                            user_id=user.user_id,
                            ts=s_ts,
                            txn_type="expense",
                            category="shopping",
                            purpose="discretionary",
                            amount=s_amt,
                            fee=Decimal("0.00"),
                            description="Eid-ul-Fitr Clothing & Family Gifts",
                            merchant=str(self.rng.choice(MERCHANTS_BY_CATEGORY["shopping"])),
                        )
                    )

            # -------------------------------------------------------------
            # D. Cash-Out Behavior & MFS Fee Charge Modeling
            # -------------------------------------------------------------
            # Frequency and volume determined by persona
            if current_persona == "cash_dominant_transactor":
                num_cashouts = int(self.rng.integers(4, 7))
                cashout_share = float(self.rng.uniform(0.65, 0.85))
            elif current_persona == "tight_budgeter" or user.occupation == "garment_worker":
                num_cashouts = int(self.rng.integers(2, 5))
                cashout_share = float(self.rng.uniform(0.40, 0.65))
            elif current_persona == "consistent_saver":
                num_cashouts = int(self.rng.integers(0, 2))
                cashout_share = float(self.rng.uniform(0.05, 0.20))
            else:
                num_cashouts = int(self.rng.integers(1, 3))
                cashout_share = float(self.rng.uniform(0.15, 0.40))

            if num_cashouts > 0:
                co_days = sorted(self.rng.choice(range(2, 28), size=num_cashouts, replace=False))
                total_co_target = base_income * cashout_share
                co_per_txn = total_co_target / float(num_cashouts)

                for co_day in co_days:
                    co_date = date(2026, month, int(co_day))
                    # Round cash-out amount to realistic hundred/thousand denominations (e.g. ৳500, ৳1000, ৳2500)
                    raw_co = round(co_per_txn * float(self.rng.uniform(0.75, 1.25)) / 100.0) * 100
                    co_amt = Decimal(str(max(100.0, raw_co))).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                    co_ts = self.calendar.make_dhaka_datetime(
                        co_date, int(self.rng.integers(11, 20)), int(self.rng.integers(0, 60))
                    )

                    # 1.85% MFS Fee charge
                    fee_pct = (
                        Decimal("0.0185") if self.rng.random() < 0.70 else Decimal("0.0149")
                    )  # Priyo agent
                    co_fee = (co_amt * fee_pct).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                    # Main cash-out transaction
                    events.append(
                        RawEvent(
                            event_id=self._make_uuid(),
                            user_id=user.user_id,
                            ts=co_ts,
                            txn_type="cash_out",
                            category="cash_out",
                            purpose="necessity",
                            amount=co_amt,
                            fee=co_fee,
                            description="MFS Agent Point Cash-Out",
                            merchant="MFS Authorized Agent",
                        )
                    )

                    # Linked separate MFS Fee expense row (as mandated by acceptance contract)
                    fee_ts = co_ts + timedelta(seconds=2)
                    events.append(
                        RawEvent(
                            event_id=self._make_uuid(),
                            user_id=user.user_id,
                            ts=fee_ts,
                            txn_type="expense",
                            category="mfs_fee",
                            purpose="necessity",
                            amount=co_fee,
                            fee=Decimal("0.00"),
                            description="MFS Cash-Out Service Charge (1.85%)",
                            merchant="MFS System Service",
                        )
                    )

        # -----------------------------------------------------------------
        # E. Labeling Noise: 5% to 8% mislabeled purpose or "other"
        # -----------------------------------------------------------------
        for ev in events:
            if ev.txn_type == "expense" and ev.purpose and self.rng.random() < 0.06:
                # Either flip purpose or mark "other"
                ev.purpose = str(self.rng.choice(["necessity", "discretionary", "other"]))

        return events
