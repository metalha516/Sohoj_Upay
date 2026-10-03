"""Pydantic v2 validation models for synthetic generator configurations."""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

# =============================================================================
# 1. Taxonomy Configuration Models
# =============================================================================


class PurposeDef(BaseModel):
    """Definition of high-level transaction purpose."""

    code: Literal["necessity", "savings_goal", "discretionary", "other"]
    description: str


class CategoryDef(BaseModel):
    """Detailed transaction category definition."""

    code: str
    name: str
    bangla_name: str
    flow_type: Literal["inflow", "outflow"]
    default_purpose: Literal["necessity", "savings_goal", "discretionary", "other"]
    is_income: bool
    typical_min_bdt: Decimal = Field(..., ge=0)
    typical_max_bdt: Decimal = Field(..., gt=0)
    typical_frequency: Literal["daily", "weekly", "bi_weekly", "monthly", "sporadic"]
    rationale: str

    @model_validator(mode="after")
    def validate_bdt_bounds(self) -> "CategoryDef":
        if self.typical_min_bdt > self.typical_max_bdt:
            raise ValueError(
                f"typical_min_bdt ({self.typical_min_bdt}) cannot exceed typical_max_bdt ({self.typical_max_bdt}) "
                f"for category '{self.code}'"
            )
        return self


class TaxonomyConfig(BaseModel):
    """Root configuration for MFS taxonomy."""

    purposes: list[PurposeDef]
    categories: list[CategoryDef]


# =============================================================================
# 2. Persona Configuration Models
# =============================================================================


class IncomeBandDef(BaseModel):
    min_bdt: Decimal = Field(..., ge=0)
    median_bdt: Decimal = Field(..., gt=0)
    max_bdt: Decimal = Field(..., gt=0)

    @model_validator(mode="after")
    def validate_income_band(self) -> "IncomeBandDef":
        if not (self.min_bdt <= self.median_bdt <= self.max_bdt):
            raise ValueError("Income band must satisfy min_bdt <= median_bdt <= max_bdt")
        return self


class SavingsRateDef(BaseModel):
    mean: Decimal = Field(..., ge=0, le=1)
    std_dev: Decimal = Field(..., ge=0)
    min: Decimal = Field(..., ge=0)
    max: Decimal = Field(..., le=1)

    @model_validator(mode="after")
    def validate_savings_rate_bounds(self) -> "SavingsRateDef":
        if not (self.min <= self.mean <= self.max):
            raise ValueError("Savings rate bounds must satisfy min <= mean <= max")
        return self


class SpendMixDef(BaseModel):
    necessity_share: Decimal = Field(..., ge=0, le=1)
    discretionary_share: Decimal = Field(..., ge=0, le=1)
    savings_goal_share: Decimal = Field(..., ge=0, le=1)
    other_share: Decimal = Field(..., ge=0, le=1)

    @model_validator(mode="after")
    def validate_sum_to_one(self) -> "SpendMixDef":
        total = (
            self.necessity_share
            + self.discretionary_share
            + self.savings_goal_share
            + self.other_share
        )
        if abs(total - Decimal("1.00")) > Decimal("0.001"):
            raise ValueError(f"Spend mix shares must sum to 1.00 (got {total})")
        return self


class CashoutBehaviorDef(BaseModel):
    frequency_per_month_mean: Decimal = Field(..., ge=0)
    volume_ratio_mean: Decimal = Field(..., ge=0, le=1)


class GoalBehaviorDef(BaseModel):
    active_goals_mean: Decimal = Field(..., ge=0)
    goal_adherence_rate: Decimal = Field(..., ge=0, le=1)
    typical_target_horizon_months: int = Field(..., gt=0)


class PersonaDef(BaseModel):
    code: str
    name: str
    target_population_share: Decimal = Field(..., gt=0, le=1)
    description: str
    income_band: IncomeBandDef
    income_regularity: Literal[
        "regular_monthly", "bi_weekly", "weekly_irregular", "lumpy_milestone"
    ]
    savings_rate: SavingsRateDef
    spend_mix: SpendMixDef
    cashout_behavior: CashoutBehaviorDef
    expense_variance: Literal["low", "moderate", "high", "extreme"]
    goal_behavior: GoalBehaviorDef


class PersonasConfig(BaseModel):
    personas: list[PersonaDef]

    @model_validator(mode="after")
    def validate_population_share_sum(self) -> "PersonasConfig":
        total_share = sum((p.target_population_share for p in self.personas), Decimal("0"))
        if abs(total_share - Decimal("1.00")) > Decimal("0.001"):
            raise ValueError(f"Total target population share must sum to 1.00 (got {total_share})")
        return self


# =============================================================================
# 3. Occupation Configuration Models
# =============================================================================


class IncomeDistributionDef(BaseModel):
    min: Decimal = Field(..., ge=0)
    p10: Decimal = Field(..., ge=0)
    p25: Decimal = Field(..., ge=0)
    median: Decimal = Field(..., ge=0)
    p75: Decimal = Field(..., ge=0)
    p90: Decimal = Field(..., ge=0)
    max: Decimal = Field(..., ge=0)

    @model_validator(mode="after")
    def validate_percentiles(self) -> "IncomeDistributionDef":
        vals = [self.min, self.p10, self.p25, self.median, self.p75, self.p90, self.max]
        if vals != sorted(vals):
            raise ValueError(f"Income percentiles must be strictly non-decreasing: {vals}")
        return self


class OccupationDef(BaseModel):
    code: str
    name: str
    bangla_name: str
    description: str
    income_distribution_bdt: IncomeDistributionDef
    persona_mapping: dict[str, Decimal]

    @field_validator("persona_mapping")
    @classmethod
    def validate_mapping_sum(cls, v: dict[str, Decimal]) -> dict[str, Decimal]:
        total = sum(v.values(), Decimal("0"))
        if abs(total - Decimal("1.00")) > Decimal("0.001"):
            raise ValueError(f"Persona mapping probabilities must sum to 1.00 (got {total})")
        return v


class OccupationsConfig(BaseModel):
    occupations: list[OccupationDef]


# =============================================================================
# 4. Anomaly Configuration Models
# =============================================================================


class AnomalyTypeDef(BaseModel):
    code: str
    name: str
    description: str
    probability: Decimal = Field(..., ge=0, le=1)
    min_multiplier: Decimal | None = None
    max_multiplier: Decimal | None = None
    allowed_hours: list[int] | None = None
    typical_categories: list[str] | None = None
    burst_count_min: int | None = None
    burst_count_max: int | None = None
    window_minutes: int | None = None


class LifeEventDef(BaseModel):
    code: str
    name: str
    description: str
    annual_probability_per_user: Decimal = Field(..., ge=0, le=1)
    typical_cost_range_bdt: list[Decimal] | None = None
    category: str | None = None
    duration_months: int | None = None


class AnomaliesConfig(BaseModel):
    target_injection_rate: Decimal = Field(..., ge=0, le=Decimal("0.10"))
    anomaly_types: list[AnomalyTypeDef]
    life_events: list[LifeEventDef]

    @model_validator(mode="after")
    def validate_anomaly_types_sum(self) -> "AnomaliesConfig":
        total_prob = sum((a.probability for a in self.anomaly_types), Decimal("0"))
        if abs(total_prob - Decimal("1.00")) > Decimal("0.001"):
            raise ValueError(f"Anomaly type probabilities must sum to 1.00 (got {total_prob})")
        return self


# =============================================================================
# 5. Calendar Configuration Models
# =============================================================================


class FestivalDef(BaseModel):
    name: str
    start_date: str | None = None
    end_date: str | None = None
    date: str | None = None
    festival_start: str | None = None
    festival_end: str | None = None
    shopping_start: str | None = None
    shopping_end: str | None = None
    bonus_window_start: str | None = None
    bonus_window_end: str | None = None
    qurbani_window_start: str | None = None
    qurbani_window_end: str | None = None
    effects: dict[str, Decimal | bool | int | float] = Field(default_factory=dict)


class SalaryCycleDef(BaseModel):
    cluster: str
    start_day: int
    end_day: int


class BillDaysDef(BaseModel):
    rent: dict[str, int]
    utilities: dict[str, int]
    education_terms: list[int]


class CyclesDef(BaseModel):
    salary_days: dict[str, SalaryCycleDef]
    bill_days: BillDaysDef


class CalendarConfig(BaseModel):
    timezone: str = "Asia/Dhaka"
    year: int = 2026
    start_date: str = "2026-01-01"
    end_date: str = "2026-12-31"
    weekend_days: list[int] = Field(default_factory=lambda: [4, 5])
    festivals: dict[str, FestivalDef]
    cycles: CyclesDef
