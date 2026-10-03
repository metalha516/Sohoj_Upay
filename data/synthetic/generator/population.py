import sys
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import numpy as np
import yaml

# Ensure backend/ is on sys.path for app.* imports
_backend_dir = Path(__file__).resolve().parents[3] / "backend"
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from app.schemas.synthetic_config import OccupationsConfig, PersonasConfig  # noqa: E402

BD_FIRST_NAMES = [
    "Mohammad",
    "Md.",
    "Ahmed",
    "Mahmudul",
    "Tanvir",
    "Sakib",
    "Rakib",
    "Anisur",
    "Kamrul",
    "Rashed",
    "Shakil",
    "Arifur",
    "Habibur",
    "Mostafa",
    "Sohag",
    "Farhana",
    "Nusrat",
    "Sadia",
    "Tahmina",
    "Afroza",
    "Jannatul",
    "Sharmin",
    "Tasnim",
    "Sultana",
    "Roksana",
    "Shamima",
    "Sabina",
    "Nasreen",
    "Zannat",
    "Nazmul",
    "Kazi",
    "Shahadat",
    "Biplob",
    "Mehedi",
    "Zubair",
    "Sumaiya",
]

BD_LAST_NAMES = [
    "Rahman",
    "Islam",
    "Hossain",
    "Hasan",
    "Chowdhury",
    "Begum",
    "Akter",
    "Khan",
    "Ahmed",
    "Uddin",
    "Sarkar",
    "Ali",
    "Haque",
    "Bhuiyan",
    "Miah",
    "Talukder",
    "Khatun",
    "Dewan",
    "Mallick",
    "Sikder",
    "Majumder",
]

BD_OPERATOR_PREFIXES = ["+88017", "+88018", "+88019", "+88013", "+88014", "+88015", "+88016"]

GOAL_TEMPLATES = [
    ("emergency_fund", "Emergency Fund", Decimal("20000"), Decimal("60000"), 6),
    ("smartphone", "Smartphone Upgrade", Decimal("15000"), Decimal("35000"), 4),
    ("laptop_purchase", "Laptop for Work/Study", Decimal("40000"), Decimal("90000"), 8),
    ("motorbike", "Commuter Motorbike Downpayment", Decimal("60000"), Decimal("140000"), 10),
    ("wedding_expenses", "Family Wedding Gift & Savings", Decimal("30000"), Decimal("100000"), 9),
    ("hajj_umrah", "Umrah Savings Fund", Decimal("80000"), Decimal("220000"), 12),
    ("higher_education", "Semester Tuition Savings", Decimal("25000"), Decimal("75000"), 5),
]


@dataclass
class SyntheticGoal:
    goal_id: uuid.UUID
    user_id: uuid.UUID
    title: str
    category: str
    target_amount: Decimal
    current_amount: Decimal
    target_date: date
    status: str = "active"


@dataclass
class SyntheticUser:
    user_id: uuid.UUID
    email: str
    phone: str
    full_name: str
    occupation: str
    persona: str
    baseline_income: Decimal
    starting_balance: Decimal
    rent_status: str  # "renter" or "owner_living_with_family"
    is_drifting: bool
    secondary_persona: str | None
    drift_month: int | None
    has_festival_bonus: bool
    goals: list[SyntheticGoal] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


class PopulationGenerator:
    """Generates realistic Bangladeshi MFS users, occupations, personas, and financial goals."""

    def __init__(self, config_dir: Path | None = None, seed: int = 42) -> None:
        if config_dir is None:
            config_dir = Path("data/synthetic/config")
        self.config_dir = config_dir
        self.rng = np.random.default_rng(seed)

        # Load occupations config
        with open(config_dir / "occupations.yaml", encoding="utf-8") as f:
            occ_data = yaml.safe_load(f)
        self.occupations_config = OccupationsConfig.model_validate(occ_data)

        # Load personas config
        with open(config_dir / "personas.yaml", encoding="utf-8") as f:
            persona_data = yaml.safe_load(f)
        self.personas_config = PersonasConfig.model_validate(persona_data)

    def generate_users(self, n: int = 600) -> list[SyntheticUser]:
        """Generate N realistic Bangladeshi users with calibrated demographics."""
        users: list[SyntheticUser] = []

        occ_codes = [o.code for o in self.occupations_config.occupations]
        occ_weights = {
            "garment_worker": 0.18,
            "student": 0.12,
            "private_sector_employee": 0.16,
            "government_employee": 0.10,
            "freelancer_gig_worker": 0.12,
            "small_shopkeeper_merchant": 0.14,
            "ride_share_driver": 0.10,
            "homemaker_remittance_recipient": 0.08,
        }
        raw_probs = [
            occ_weights.get(o.code, 1.0 / len(occ_codes))
            for o in self.occupations_config.occupations
        ]
        total_p = sum(raw_probs)
        occ_probs = [p / total_p for p in raw_probs]

        selected_occs = self.rng.choice(occ_codes, size=n, p=occ_probs)

        # Pre-lookup dictionary of occupations
        occ_lookup = {o.code: o for o in self.occupations_config.occupations}

        for occ_code in selected_occs:
            user_id = uuid.UUID(bytes=bytes(self.rng.bytes(16)))
            first_name = self.rng.choice(BD_FIRST_NAMES)
            last_name = self.rng.choice(BD_LAST_NAMES)
            full_name = f"{first_name} {last_name}"

            # Clean name for safe email
            email_first = first_name.lower().replace(".", "").replace(" ", "")
            email_last = last_name.lower().replace(".", "").replace(" ", "")
            email = f"{email_first}.{email_last}.{user_id.hex[:6]}@example.test"

            # Phone number with valid BD MFS operator prefix
            prefix = self.rng.choice(BD_OPERATOR_PREFIXES)
            rest_digits = f"{self.rng.integers(10000000, 99999999):08d}"
            phone = f"{prefix}{rest_digits[:8]}"

            occ_def = occ_lookup[occ_code]

            # Sample baseline monthly income from lognormal distribution
            # using median and percentiles
            inc_dist = occ_def.income_distribution_bdt
            median_inc = float(inc_dist.median)
            p90_inc = float(inc_dist.p90)
            min_inc = float(inc_dist.min)
            max_inc = float(inc_dist.max)

            sigma = max(0.20, (np.log(p90_inc) - np.log(median_inc)) / 1.28)
            mu = np.log(median_inc)
            sampled_income = np.clip(self.rng.lognormal(mu, sigma), min_inc, max_inc)
            baseline_income = Decimal(str(round(sampled_income, 2))).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            # Sample persona from occupation transition mapping
            persona_codes = list(occ_def.persona_mapping.keys())
            persona_weights = [float(w) for w in occ_def.persona_mapping.values()]
            total_w = sum(persona_weights)
            persona_probs = [w / total_w for w in persona_weights]
            primary_persona = str(self.rng.choice(persona_codes, p=persona_probs))

            # Mixed / drifting assignment: ~10% probability
            is_drifting = bool(self.rng.random() < 0.10)
            secondary_persona: str | None = None
            drift_month: int | None = None
            if is_drifting:
                drift_month = int(self.rng.choice([5, 6, 7, 8]))
                other_personas = [p for p in persona_codes if p != primary_persona]
                if other_personas:
                    secondary_persona = str(self.rng.choice(other_personas))
                else:
                    secondary_persona = (
                        "discretionary_spender"
                        if primary_persona != "discretionary_spender"
                        else "tight_budgeter"
                    )

            # Starting wallet balance: 5% to 35% of monthly income
            balance_pct = self.rng.uniform(0.05, 0.35)
            raw_start_bal = max(200.0, float(baseline_income) * balance_pct)
            starting_balance = Decimal(str(round(raw_start_bal, 2))).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            # Rent status: ~80% pay rent, ~20% own or live with family
            rent_status = "renter" if self.rng.random() < 0.80 else "owner_living_with_family"

            # Eligible for festival bonus: corporate, govt, garment workers
            has_festival_bonus = occ_code in (
                "government_employee",
                "private_sector_employee",
                "garment_worker",
            )

            # Goals generation: ~60% of users have 1-3 goals
            goals: list[SyntheticGoal] = []
            if self.rng.random() < 0.60:
                num_goals = int(self.rng.choice([1, 2, 3], p=[0.60, 0.30, 0.10]))
                selected_goal_indices = self.rng.choice(
                    len(GOAL_TEMPLATES), size=min(num_goals, len(GOAL_TEMPLATES)), replace=False
                )
                for g_idx in selected_goal_indices:
                    g_cat, g_title, g_min, g_max, g_months = GOAL_TEMPLATES[g_idx]
                    # Scale goal target amount by user's income capacity
                    income_factor = max(0.6, min(2.5, float(baseline_income) / 30000.0))
                    target_bdt = Decimal(
                        str(
                            round(
                                float(self.rng.uniform(float(g_min), float(g_max))) * income_factor,
                                -2,
                            )
                        )
                    )
                    # Target date in late 2026 or 2027
                    target_month = min(12, max(3, g_months + int(self.rng.integers(-1, 3))))
                    target_date = date(2026, target_month, int(self.rng.integers(15, 28)))
                    goals.append(
                        SyntheticGoal(
                            goal_id=uuid.UUID(bytes=bytes(self.rng.bytes(16))),
                            user_id=user_id,
                            title=g_title,
                            category=g_cat,
                            target_amount=target_bdt,
                            current_amount=Decimal("0.00"),
                            target_date=target_date,
                            status="active",
                        )
                    )

            user = SyntheticUser(
                user_id=user_id,
                email=email,
                phone=phone,
                full_name=full_name,
                occupation=occ_code,
                persona=primary_persona,
                baseline_income=baseline_income,
                starting_balance=starting_balance,
                rent_status=rent_status,
                is_drifting=is_drifting,
                secondary_persona=secondary_persona,
                drift_month=drift_month,
                has_festival_bonus=has_festival_bonus,
                goals=goals,
            )
            users.append(user)

        return users
