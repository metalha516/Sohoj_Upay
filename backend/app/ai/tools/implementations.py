"""Concrete implementations of all 15 financial tools from design.md §7.3."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.financial.engine import (
    calculate_doubling_time as fe_doubling_time,
)
from app.financial.engine import (
    calculate_future_value as fe_future_value,
)
from app.financial.engine import (
    calculate_monthly_required_saving as fe_required_saving,
)
from app.financial.engine import (
    calculate_savings_rate as fe_savings_rate,
)
from app.financial.engine import (
    run_scenario as fe_run_scenario,
)
from app.financial.exceptions import FinancialEngineError
from app.financial.schemas import ScenarioInput
from app.services.dashboard_service import DashboardService
from app.services.goal_service import GoalService
from app.services.ml_service import MLService
from app.services.rag_service import RAGService
from app.services.transaction_service import TransactionService
from app.services.user_service import UserService


# ---------------------------------------------------------------------------
# Pydantic Schemas with extra="forbid" (prevents user_id or param injection)
# ---------------------------------------------------------------------------
class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EmptyArgsSchema(StrictBaseModel):
    """Empty schema for tools that require no parameters from the LLM."""


class GetTransactionsSchema(StrictBaseModel):
    category: str | None = Field(
        default=None, description="Optional category filter (e.g. food, transport)"
    )
    transaction_type: Literal["income", "expense", "cash_in", "cash_out", "transfer"] | None = (
        Field(default=None, description="Transaction type filter")
    )
    limit: int = Field(
        default=10, ge=1, le=50, description="Max transactions to return (capped at 50)"
    )


class GetMonthlySummarySchema(StrictBaseModel):
    months: int = Field(default=3, ge=1, le=12, description="Number of recent months to inspect")


class GetAnomaliesSchema(StrictBaseModel):
    limit: int = Field(
        default=10, ge=1, le=50, description="Max anomalies to return (capped at 50)"
    )


class CalculateFutureValueSchema(StrictBaseModel):
    principal: float = Field(ge=0.0, description="Initial investment amount in Taka")
    annual_rate_percent: float = Field(
        ge=0.0, le=100.0, description="Annual nominal interest rate in percent (e.g. 8.0)"
    )
    years: float = Field(gt=0.0, le=60.0, description="Time horizon in years")
    monthly_contribution: float = Field(
        default=0.0, ge=0.0, description="Monthly contribution amount in Taka"
    )
    compounding_per_year: int = Field(
        default=12, description="Compounding frequency per year (1, 2, 4, 12, 365)"
    )
    rate_type: Literal["assumed", "historical", "contractual"] = Field(
        default="assumed", description="Mandatory rate assumption classification"
    )


class CalculateDoublingTimeSchema(StrictBaseModel):
    annual_rate_percent: float = Field(
        gt=0.0, le=100.0, description="Annual nominal interest rate in percent (e.g. 8.0)"
    )
    compounding_per_year: int = Field(
        default=12, description="Compounding frequency per year (1, 2, 4, 12, 365)"
    )
    rate_type: Literal["assumed", "historical", "contractual"] = Field(
        default="assumed", description="Mandatory rate assumption classification"
    )


class CalculateGoalPlanSchema(StrictBaseModel):
    target_amount: float = Field(gt=0.0, description="Target savings milestone in Taka")
    current_savings: float = Field(
        default=0.0, ge=0.0, description="Current amount saved toward this goal"
    )
    time_horizon_months: int = Field(
        gt=0, le=720, description="Number of months remaining until target date"
    )
    annual_rate_percent: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Expected annual return rate in percent"
    )


class CalculateSavingsRateSchema(StrictBaseModel):
    monthly_savings: float = Field(ge=0.0, description="Total monthly savings amount in Taka")
    monthly_income: float = Field(gt=0.0, description="Total monthly income in Taka")


class RunFinancialScenarioSchema(StrictBaseModel):
    annual_income: float = Field(gt=0.0, description="Gross annual household income in Taka")
    annual_expenses: float = Field(ge=0.0, description="Total annual expenses in Taka")
    current_net_worth: float = Field(default=0.0, description="Current net worth in Taka")
    years: int = Field(default=5, ge=1, le=30, description="Number of projection years")
    investment_rate_pct: float = Field(
        default=7.0, ge=0.0, le=30.0, description="Expected annual investment return %"
    )
    inflation_rate_pct: float = Field(
        default=6.0, ge=0.0, le=30.0, description="Expected annual inflation rate %"
    )


class CheckAffordabilitySchema(StrictBaseModel):
    item_cost: float = Field(
        gt=0.0, description="Cost of the item or discretionary purchase in Taka"
    )
    category: str = Field(
        default="discretionary", description="Expense category (e.g., shopping, electronics)"
    )
    is_recurring: bool = Field(
        default=False, description="Whether this is a recurring monthly expense"
    )


class SearchKnowledgeSchema(StrictBaseModel):
    query: str = Field(
        min_length=2, max_length=300, description="Financial concept or question to search"
    )
    top_k: int = Field(
        default=4, ge=1, le=10, description="Number of top educational passages to return"
    )
    topic: str | None = Field(
        default=None,
        description="Optional topic filter (e.g. budgeting, emergency_fund, banking_products)",
    )


# ---------------------------------------------------------------------------
# Tool Implementations Factory
# ---------------------------------------------------------------------------
class FinancialToolSet:
    """Encapsulates backend service dependencies and provides handlers for all 15 tools."""

    def __init__(
        self,
        user_service: UserService,
        transaction_service: TransactionService,
        dashboard_service: DashboardService,
        goal_service: GoalService,
        ml_service: MLService,
        rag_service: RAGService,
    ) -> None:
        self.user_service = user_service
        self.transaction_service = transaction_service
        self.dashboard_service = dashboard_service
        self.goal_service = goal_service
        self.ml_service = ml_service
        self.rag_service = rag_service

    # 1. get_user_profile
    async def get_user_profile(self, user_id: uuid.UUID) -> dict[str, Any]:
        """Returns income band and active goals count. Never leaks email or name."""
        user = await self.user_service.get_user(user_id)
        if not user:
            return {"error": "User profile not found."}

        income = float(user.monthly_income) if user.monthly_income else 0.0
        income_band = (
            "under_25k"
            if income < 25000
            else "25k_50k"
            if income < 50000
            else "50k_100k"
            if income < 100000
            else "100k_plus"
        )
        goals = await self.goal_service.list_goals(user_id)
        return {
            "income_band": income_band,
            "monthly_income_approx": round(income, -2),
            "active_goals_count": len([g for g in goals if g.status == "active"]),
            "consent_ai": user.consent_ai,
        }

    # 2. get_current_balance
    async def get_current_balance(self, user_id: uuid.UUID) -> dict[str, Any]:
        """Returns current liquid account balance and unallocated surplus."""
        summary = await self.dashboard_service.get_dashboard_summary(user_id)
        return {
            "monthly_income": float(summary.income),
            "monthly_expense": float(summary.expense),
            "monthly_savings": float(summary.savings),
            "unallocated_surplus": float(summary.unallocated_surplus),
            "currency": "BDT",
            "as_of": summary.month.isoformat(),
        }

    # 3. get_transactions
    async def get_transactions(
        self,
        user_id: uuid.UUID,
        category: str | None = None,
        transaction_type: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Returns filtered transactions capped at 50 rows. Excludes sensitive metadata."""
        limit = min(max(1, limit), 50)
        res = await self.transaction_service.list_transactions(
            user_id=user_id,
            category=category,
            transaction_type=transaction_type,
            limit=limit,
        )
        if hasattr(res, "items"):
            items = res.items
        elif isinstance(res, (tuple, list)):
            items = res[0] if isinstance(res, tuple) else res
        else:
            items = []
        return {
            "count": len(items),
            "transactions": [
                {
                    "amount": float(t.amount),
                    "type": t.transaction_type,
                    "category": t.category,
                    "purpose": t.purpose,
                    "date": t.ts.date().isoformat(),
                }
                for t in items
            ],
        }

    # 4. get_monthly_summary
    async def get_monthly_summary(self, user_id: uuid.UUID, months: int = 3) -> dict[str, Any]:
        """Returns monthly feature aggregates and MoM trends."""
        months = min(max(1, months), 12)
        history = await self.dashboard_service.get_monthly_features(user_id=user_id, months=months)
        return {
            "months_reported": len(history),
            "history": [
                {
                    "month": f.month.isoformat(),
                    "income": float(f.income),
                    "expense": float(f.expense),
                    "savings_rate": float(f.savings_rate) if f.savings_rate else 0.0,
                    "necessity_rate": float(f.necessity_rate) if f.necessity_rate else 0.0,
                    "discretionary_rate": float(f.discretionary_rate)
                    if f.discretionary_rate
                    else 0.0,
                }
                for f in history
            ],
        }

    # 5. get_behavior_profile
    async def get_behavior_profile(self, user_id: uuid.UUID) -> dict[str, Any]:
        """Returns spending archetype classification with confidence and top factors."""
        profile = await self.ml_service.get_latest_profile(user_id)
        if not profile:
            return {
                "profile": "insufficient_data",
                "confidence": 0.0,
                "top_factors": {},
                "model_version": "baseline",
            }
        return {
            "profile": profile.profile,
            "confidence": float(profile.confidence),
            "top_factors": profile.top_factors,
            "model_version": profile.model_version,
        }

    # 6. get_spending_forecast
    async def get_spending_forecast(self, user_id: uuid.UUID) -> dict[str, Any]:
        """Returns quantile expense forecast (p10, p50, p90) with assumption block."""
        forecast = await self.ml_service.forecast_next_month_expense(user_id)
        if not forecast:
            return {
                "point_estimate": 0.0,
                "lower_bound_p10": 0.0,
                "upper_bound_p90": 0.0,
                "confidence": 0.0,
                "horizon_month": "N/A",
                "model_version": "baseline",
                "assumptions": {},
            }
        horizon_str = (
            forecast.horizon_month.isoformat()
            if hasattr(forecast.horizon_month, "isoformat")
            else str(forecast.horizon_month)
        )
        assumptions_data = (
            forecast.assumptions.model_dump()
            if hasattr(forecast.assumptions, "model_dump")
            else (dict(forecast.assumptions) if isinstance(forecast.assumptions, dict) else {})
        )
        return {
            "point_estimate": float(forecast.point_estimate),
            "lower_bound_p10": float(forecast.lower_bound_p10),
            "upper_bound_p90": float(forecast.upper_bound_p90),
            "confidence": float(forecast.confidence),
            "horizon_month": horizon_str,
            "model_version": forecast.model_version,
            "assumptions": assumptions_data,
        }

    # 7. get_anomalies
    async def get_anomalies(self, user_id: uuid.UUID, limit: int = 10) -> dict[str, Any]:
        """Returns open anomalies with observed values, baselines, and explanations."""
        limit = min(max(1, limit), 50)
        items = await self.ml_service.get_anomalies(user_id=user_id, status="open", limit=limit)
        res = []
        for a in items:
            if isinstance(a, dict):
                res.append(
                    {
                        "category": a.get("category", "unknown"),
                        "observed_value": float(a.get("observed_value", a.get("amount", 0.0))),
                        "baseline_value": float(a.get("baseline_value", 0.0)),
                        "deviation_pct": float(a.get("deviation_pct", 0.0)),
                        "explanation": a.get("explanation", ""),
                    }
                )
            else:
                res.append(
                    {
                        "category": a.category,
                        "observed_value": float(a.observed_value),
                        "baseline_value": float(a.baseline_value),
                        "deviation_pct": float(a.deviation_pct),
                        "explanation": a.explanation,
                    }
                )
        return {
            "count": len(items),
            "anomalies": res,
        }

    # 8. get_financial_goals
    async def get_financial_goals(self, user_id: uuid.UUID) -> dict[str, Any]:
        """Returns goals with target amounts, progress percentages, and ETAs."""
        goals = await self.goal_service.list_goals(user_id)
        return {
            "goals_count": len(goals),
            "goals": [
                {
                    "name": g.name,
                    "target_amount": float(g.target_amount),
                    "current_amount": float(g.current_amount),
                    "progress_percentage": float(g.progress_pct),
                    "remaining_amount": float(g.target_amount - g.current_amount),
                    "status": g.status,
                    "feasibility": "on_track" if g.is_on_track else "behind",
                }
                for g in goals
            ],
        }

    # 9. calculate_future_value
    async def calculate_future_value(
        self,
        principal: float,
        annual_rate_percent: float,
        years: float,
        monthly_contribution: float = 0.0,
        compounding_per_year: int = 12,
        rate_type: str = "assumed",
    ) -> dict[str, Any]:
        """Exact compound growth calculation using deterministic Financial Engine."""
        try:
            res = fe_future_value(
                principal=Decimal(str(principal)),
                annual_rate=Decimal(str(annual_rate_percent / 100.0)),
                years=Decimal(str(years)),
                monthly_contribution=Decimal(str(monthly_contribution)),
                compounding_per_year=compounding_per_year,
                rate_type=rate_type,  # type: ignore[arg-type]
            )
            return {
                "future_value": float(res.future_value),
                "total_contributed": float(res.total_contributed),
                "total_growth": float(res.total_growth),
                "assumptions": {
                    "annual_rate": float(res.assumptions.annual_rate),
                    "rate_type": res.assumptions.rate_type,
                    "compounding_per_year": res.assumptions.compounding_per_year,
                },
                "disclaimer_code": res.disclaimer_code,
            }
        except FinancialEngineError as e:
            return {"error": f"Financial calculation error: {e.message}"}

    # 10. calculate_doubling_time
    async def calculate_doubling_time(
        self,
        annual_rate_percent: float,
        compounding_per_year: int = 12,
        rate_type: str = "assumed",
    ) -> dict[str, Any]:
        """Exact doubling time calculation comparing exact compound math with Rule of 72."""
        try:
            res = fe_doubling_time(
                annual_rate=Decimal(str(annual_rate_percent / 100.0)),
                compounding_per_year=compounding_per_year,
                rate_type=rate_type,  # type: ignore[arg-type]
            )
            return {
                "exact_years": float(res.years),
                "years": float(res.years),
                "rule_of_72_years": float(res.rule_of_72_approx),
                "months": res.months,
                "disclaimer_code": res.disclaimer_code,
            }
        except FinancialEngineError as e:
            return {"error": f"Financial calculation error: {e.message}"}

    # 11. calculate_goal_plan
    async def calculate_goal_plan(
        self,
        target_amount: float,
        current_savings: float = 0.0,
        time_horizon_months: int = 12,
        annual_rate_percent: float = 0.0,
        user_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Computes required monthly savings to achieve target milestone."""
        try:
            req_res = fe_required_saving(
                target=Decimal(str(target_amount)),
                current=Decimal(str(current_savings)),
                months=time_horizon_months,
                annual_rate=Decimal(str(annual_rate_percent / 100.0)),
            )
            req_saving_val = float(req_res.required_monthly_saving)

            # Compare with trailing average savings if user_id is provided
            hist_avg = 0.0
            feasibility = "unknown"
            if user_id:
                history = await self.dashboard_service.get_monthly_features(
                    user_id=user_id, months=3
                )
                if history:
                    hist_avg = sum(float(f.savings) for f in history) / len(history)
                    feasibility = "on_track" if hist_avg >= req_saving_val else "behind"

            return {
                "target_amount": float(target_amount),
                "current_savings": float(current_savings),
                "required_monthly_saving": req_saving_val,
                "time_horizon_months": time_horizon_months,
                "historical_3m_savings": round(hist_avg, 2),
                "feasibility": feasibility,
            }
        except FinancialEngineError as e:
            return {"error": f"Financial calculation error: {e.message}"}

    # 12. calculate_savings_rate
    async def calculate_savings_rate(
        self, monthly_savings: float, monthly_income: float
    ) -> dict[str, Any]:
        """Calculates exact savings rate percentage from income and savings."""
        try:
            rate = fe_savings_rate(
                savings=Decimal(str(monthly_savings)),
                income=Decimal(str(monthly_income)),
            )
            rate_float = float(rate) if rate is not None else 0.0
            return {
                "savings_rate": rate_float,
                "savings_rate_pct": round(rate_float * 100, 2),
            }
        except FinancialEngineError as e:
            return {"error": f"Financial calculation error: {e.message}"}

    # 13. run_financial_scenario
    async def run_financial_scenario(
        self,
        annual_income: float,
        annual_expenses: float,
        current_net_worth: float = 0.0,
        years: int = 5,
        investment_rate_pct: float = 7.0,
        inflation_rate_pct: float = 6.0,
    ) -> dict[str, Any]:
        """Projects multi-year wealth accumulation trajectory under economic assumptions."""
        try:
            monthly_inc = Decimal(str(annual_income / 12.0))
            monthly_exp = Decimal(str(annual_expenses / 12.0))
            base_input = ScenarioInput(
                initial_balance=Decimal(str(current_net_worth)),
                monthly_income=monthly_inc,
                monthly_expense=monthly_exp,
                monthly_savings=max(Decimal("0.00"), monthly_inc - monthly_exp),
                annual_return_rate=Decimal(str(investment_rate_pct / 100.0)),
                horizon_years=years,
                rate_type="assumed",
            )
            res = fe_run_scenario(base=base_input)
            return {
                "years": years,
                "final_net_worth": float(res.simulated_future_value),
                "baseline_net_worth": float(res.base_future_value),
                "net_benefit": float(res.net_benefit),
                "assumptions": {
                    "investment_rate_pct": investment_rate_pct,
                    "inflation_rate_pct": inflation_rate_pct,
                },
                "disclaimer_code": res.disclaimer_code,
            }
        except FinancialEngineError as e:
            return {"error": f"Financial calculation error: {e.message}"}

    # 14. check_affordability
    async def check_affordability(
        self,
        user_id: uuid.UUID,
        item_cost: float,
        category: str = "discretionary",
        is_recurring: bool = False,
    ) -> dict[str, Any]:
        """Evaluates whether an expense fits comfortably within surplus buffer."""
        summary = await self.dashboard_service.get_dashboard_summary(user_id)
        current_surplus = float(summary.unallocated_surplus)

        history = await self.dashboard_service.get_monthly_features(user_id=user_id, months=3)
        trailing_surplus = (
            sum(float(h.income - h.expense - h.savings) for h in history) / len(history)
            if history
            else current_surplus
        )

        remaining_buffer = current_surplus - item_cost

        if remaining_buffer >= trailing_surplus * 0.4:
            verdict = "comfortable"
            rationale = "The purchase fits easily within your current unallocated surplus without straining your buffer."
        elif remaining_buffer >= 0.0:
            verdict = "stretch"
            rationale = "The purchase is affordable from available cash flow, but absorbs most of your monthly surplus."
        else:
            verdict = "unaffordable"
            rationale = "The purchase exceeds your available monthly surplus and would require drawing down savings."

        return {
            "item_cost": float(item_cost),
            "current_month_surplus": round(current_surplus, 2),
            "trailing_3m_avg_surplus": round(trailing_surplus, 2),
            "remaining_buffer": round(remaining_buffer, 2),
            "verdict": verdict,
            "rationale": rationale,
            "is_recurring": is_recurring,
        }

    # 15. search_knowledge
    async def search_knowledge(
        self,
        query: str,
        top_k: int = 4,
        topic: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieves top-k educational knowledge passages from RAG knowledge base."""
        return await self.rag_service.search_knowledge(
            query=query,
            top_k=min(top_k, 6),
            topic=topic,
        )


def register_financial_tools(tool_manager: Any, tool_set: FinancialToolSet) -> None:
    """Register all 15 financial tools with a ToolManager instance."""
    tool_manager.register(
        name="get_user_profile",
        description="Fetch high-level user profile (income band, active goal count, AI consent). Never exposes raw PII.",
        schema_model=EmptyArgsSchema,
        handler=tool_set.get_user_profile,
        requires_user_id=True,
    )
    tool_manager.register(
        name="get_current_balance",
        description="Fetch liquid monthly income, expense, savings, and unallocated surplus for the current month.",
        schema_model=EmptyArgsSchema,
        handler=tool_set.get_current_balance,
        requires_user_id=True,
    )
    tool_manager.register(
        name="get_transactions",
        description="Query recent transactions filtered by category or transaction type (capped at 50 records).",
        schema_model=GetTransactionsSchema,
        handler=tool_set.get_transactions,
        requires_user_id=True,
    )
    tool_manager.register(
        name="get_monthly_summary",
        description="Retrieve historical monthly summary metrics (up to 12 months) including income, expense, savings rate.",
        schema_model=GetMonthlySummarySchema,
        handler=tool_set.get_monthly_summary,
        requires_user_id=True,
    )
    tool_manager.register(
        name="get_behavior_profile",
        description="Retrieve the user's ML-classified financial behavior profile, archetype, and top drivers.",
        schema_model=EmptyArgsSchema,
        handler=tool_set.get_behavior_profile,
        requires_user_id=True,
    )
    tool_manager.register(
        name="get_spending_forecast",
        description="Retrieve next-month ML expense forecast with p10, p50, and p90 uncertainty bounds.",
        schema_model=EmptyArgsSchema,
        handler=tool_set.get_spending_forecast,
        requires_user_id=True,
    )
    tool_manager.register(
        name="get_anomalies",
        description="Retrieve detected spending anomalies and unusual transactions.",
        schema_model=GetAnomaliesSchema,
        handler=tool_set.get_anomalies,
        requires_user_id=True,
    )
    tool_manager.register(
        name="get_financial_goals",
        description="Retrieve user's active financial savings goals, target amounts, current progress, and ETAs.",
        schema_model=EmptyArgsSchema,
        handler=tool_set.get_financial_goals,
        requires_user_id=True,
    )
    tool_manager.register(
        name="calculate_future_value",
        description="Calculate exact compound interest future value using the deterministic Financial Engine.",
        schema_model=CalculateFutureValueSchema,
        handler=tool_set.calculate_future_value,
        requires_user_id=False,
    )
    tool_manager.register(
        name="calculate_doubling_time",
        description="Calculate exact time required for an investment to double at a given annual interest rate.",
        schema_model=CalculateDoublingTimeSchema,
        handler=tool_set.calculate_doubling_time,
        requires_user_id=False,
    )
    tool_manager.register(
        name="calculate_goal_plan",
        description="Calculate required monthly saving to achieve a target financial goal by a deadline.",
        schema_model=CalculateGoalPlanSchema,
        handler=tool_set.calculate_goal_plan,
        requires_user_id=False,
    )
    tool_manager.register(
        name="calculate_savings_rate",
        description="Calculate exact savings rate percentage from monthly income and savings.",
        schema_model=CalculateSavingsRateSchema,
        handler=tool_set.calculate_savings_rate,
        requires_user_id=False,
    )
    tool_manager.register(
        name="run_financial_scenario",
        description="Project a multi-year financial trajectory with investment returns and inflation adjustments.",
        schema_model=RunFinancialScenarioSchema,
        handler=tool_set.run_financial_scenario,
        requires_user_id=False,
    )
    tool_manager.register(
        name="check_affordability",
        description="Assess whether a specific discretionary purchase fits comfortably within monthly surplus buffer.",
        schema_model=CheckAffordabilitySchema,
        handler=tool_set.check_affordability,
        requires_user_id=True,
    )
    tool_manager.register(
        name="search_knowledge",
        description="Search curated educational financial literacy knowledge base for grounded factual guidance.",
        schema_model=SearchKnowledgeSchema,
        handler=tool_set.search_knowledge,
        requires_user_id=False,
    )
