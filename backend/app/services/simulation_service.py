"""Service wrapping the deterministic financial engine for simulation endpoints."""

from __future__ import annotations

from typing import Any

from app.financial.engine import (
    calculate_doubling_time,
    calculate_future_value,
    calculate_monthly_required_saving,
    run_scenario,
)
from app.financial.schemas import AssumptionsBlock, ScenarioInput
from app.schemas.simulation import (
    ScenarioYearPointSchema,
    SimulateDoublingRequest,
    SimulateDoublingResponse,
    SimulateGoalRequest,
    SimulateGoalResponse,
    SimulateGrowthRequest,
    SimulateGrowthResponse,
    SimulateScenarioRequest,
    SimulateScenarioResponse,
    YearlyPointSchema,
)


class SimulationService:
    """Service providing exact, deterministic projections via Financial Engine."""

    def simulate_growth(self, req: SimulateGrowthRequest) -> SimulateGrowthResponse:
        """Simulate compound growth and future value with periodic contributions."""
        fv_res = calculate_future_value(
            principal=req.initial_deposit,
            annual_rate=req.annual_rate,
            years=req.years,
            monthly_contribution=req.monthly_contribution,
            compounding_per_year=req.compounding_per_year,
            contribution_timing=req.timing,
            rate_type=req.rate_type,
            inflation_adjusted=req.inflation_adjusted,
        )

        series_schemas = [
            YearlyPointSchema(
                year=yp.year,
                balance=yp.balance,
                contributions=yp.contributions,
                growth=yp.growth,
            )
            for yp in fv_res.series
        ]

        return SimulateGrowthResponse(
            future_value=fv_res.future_value,
            total_contributed=fv_res.total_contributed,
            total_growth=fv_res.total_growth,
            series=series_schemas,
            assumptions=self._assumptions_to_dict(fv_res.assumptions),
            disclaimer_code=fv_res.disclaimer_code,
        )

    def simulate_goal(self, req: SimulateGoalRequest) -> SimulateGoalResponse:
        """Simulate monthly savings requirement to attain a targeted sum."""
        goal_res = calculate_monthly_required_saving(
            target=req.target_amount,
            current=req.current_amount,
            months=req.months,
            annual_rate=req.annual_rate,
            rate_type=req.rate_type,
            contribution_timing=req.contribution_timing,
        )

        return SimulateGoalResponse(
            required_monthly_saving=goal_res.required_monthly_saving,
            target_amount=goal_res.target_amount,
            current_amount=goal_res.current_amount,
            shortfall=goal_res.shortfall,
            months=goal_res.months,
            total_contributed=goal_res.total_contributed,
            projected_growth=goal_res.projected_growth,
            assumptions=self._assumptions_to_dict(goal_res.assumptions),
            disclaimer_code=goal_res.disclaimer_code,
        )

    def simulate_doubling(self, req: SimulateDoublingRequest) -> SimulateDoublingResponse:
        """Simulate asset doubling period using compound closed form and Rule of 72."""
        d_res = calculate_doubling_time(
            annual_rate=req.annual_rate,
            compounding_per_year=req.compounding_per_year,
            rate_type=req.rate_type,
        )

        return SimulateDoublingResponse(
            years=d_res.years,
            months=d_res.months,
            annual_rate=d_res.annual_rate,
            rule_of_72_approx=d_res.rule_of_72_approx,
            compounding_per_year=d_res.compounding_per_year,
            assumptions=self._assumptions_to_dict(d_res.assumptions),
            disclaimer_code=d_res.disclaimer_code,
        )

    def simulate_scenario(self, req: SimulateScenarioRequest) -> SimulateScenarioResponse:
        """Simulate comparative trajectory between baseline and modified cashflows."""
        base_input = ScenarioInput(
            initial_balance=req.baseline.initial_balance,
            monthly_income=req.baseline.monthly_income,
            monthly_expense=req.baseline.monthly_expense,
            monthly_savings=req.baseline.monthly_savings,
            annual_return_rate=req.baseline.annual_return_rate,
            horizon_years=req.baseline.horizon_years,
            rate_type=req.baseline.rate_type,
        )
        overrides = {
            "initial_balance": req.simulated.initial_balance,
            "monthly_income": req.simulated.monthly_income,
            "monthly_expense": req.simulated.monthly_expense,
            "monthly_savings": req.simulated.monthly_savings,
            "annual_return_rate": req.simulated.annual_return_rate,
            "horizon_years": req.simulated.horizon_years,
        }

        scen_res = run_scenario(base=base_input, overrides=overrides)

        comparisons = [
            ScenarioYearPointSchema(
                year=cp.year,
                baseline_balance=cp.baseline_balance,
                simulated_balance=cp.simulated_balance,
                baseline_growth=cp.baseline_growth,
                simulated_growth=cp.simulated_growth,
                delta=cp.delta,
            )
            for cp in scen_res.yearly_comparison
        ]

        return SimulateScenarioResponse(
            base_future_value=scen_res.base_future_value,
            simulated_future_value=scen_res.simulated_future_value,
            net_benefit=scen_res.net_benefit,
            yearly_comparison=comparisons,
            summary=scen_res.summary,
            assumptions=self._assumptions_to_dict(scen_res.assumptions),
            disclaimer_code=scen_res.disclaimer_code,
        )

    def _assumptions_to_dict(self, assumptions: AssumptionsBlock) -> dict[str, Any]:
        """Convert AssumptionsBlock dataclass to serializable dict."""
        return {
            "rate_type": assumptions.rate_type,
            "annual_rate": str(assumptions.annual_rate),
            "compounding_per_year": assumptions.compounding_per_year,
            "contribution_timing": assumptions.contribution_timing,
            "inflation_adjusted": assumptions.inflation_adjusted,
            "metadata": assumptions.metadata,
        }
