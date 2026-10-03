"""Context builder producing minimal, anonymized, compact user financial context."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.services.dashboard_service import DashboardService
from app.services.goal_service import GoalService
from app.services.ml_service import MLService

logger = logging.getLogger(__name__)


@dataclass
class UserContext:
    """Anonymized, compact user context for LLM turns."""

    formatted_context: str
    data_manifest: dict[str, Any]
    grounding_numbers: set[float] = field(default_factory=set)


class ContextBuilder:
    """Builds compact aggregates with zero PII and logs per-request data manifests."""

    def __init__(
        self,
        dashboard_service: DashboardService,
        goal_service: GoalService,
        ml_service: MLService,
    ) -> None:
        self.dashboard_service = dashboard_service
        self.goal_service = goal_service
        self.ml_service = ml_service

    async def build_context(self, user_id: uuid.UUID) -> UserContext:
        """Fetch minimal aggregates for user and build compact context block.

        Security & Privacy rules:
        - Never includes user name, email, phone number, or account numbers.
        - Never dumps raw transaction records in prompt context.
        - Produces an explicit data manifest for audit logging.
        - Extracts all provided numbers for downstream numeric grounding checks.
        """
        grounding_nums: set[float] = set()
        manifest_fields: list[str] = []

        # 1. Fetch current month summary
        try:
            summary = await self.dashboard_service.get_dashboard_summary(user_id)
            current_income = float(summary.income)
            current_expense = float(summary.expense)
            current_savings = float(summary.savings)
            current_surplus = float(summary.unallocated_surplus)
            savings_rate = float(summary.savings_rate) if summary.savings_rate is not None else None

            grounding_nums.update(
                {current_income, current_expense, current_savings, current_surplus}
            )
            if savings_rate is not None:
                grounding_nums.add(round(savings_rate * 100, 1))
                grounding_nums.add(round(savings_rate, 4))
            manifest_fields.append("dashboard_summary")
        except Exception as e:
            logger.warning("Could not fetch dashboard summary for context: %s", e)
            current_income = 0.0
            current_expense = 0.0
            current_savings = 0.0
            current_surplus = 0.0
            savings_rate = None

        # 2. Fetch trailing 3-month features for context
        try:
            features = await self.dashboard_service.get_monthly_features(user_id=user_id, months=3)
            has_history = len(features) > 0
            if has_history:
                manifest_fields.append(f"monthly_features_trailing_{len(features)}m")
                for f in features:
                    grounding_nums.add(float(f.income))
                    grounding_nums.add(float(f.expense))
                    grounding_nums.add(float(f.savings))
                    if f.savings_rate is not None:
                        sr_val = float(f.savings_rate)
                        grounding_nums.add(round(sr_val * 100, 1))
                        grounding_nums.add(round(sr_val, 4))
        except Exception as e:
            logger.warning("Could not fetch monthly features for context: %s", e)
            has_history = False

        # 3. Fetch active goals summary (counts & targets, no private notes)
        try:
            goals = await self.goal_service.list_goals(user_id)
            active_goals = [g for g in goals if g.status == "active"]
            manifest_fields.append(f"goals_count_{len(active_goals)}")
            for g in active_goals:
                grounding_nums.add(float(g.target_amount))
                grounding_nums.add(float(g.current_amount))
                if g.progress_pct is not None:
                    grounding_nums.add(round(float(g.progress_pct), 1))
        except Exception as e:
            logger.warning("Could not fetch goals for context: %s", e)
            active_goals = []

        # 4. Fetch behavior profile if available
        profile_label = "Insufficient Data"
        try:
            profile = await self.ml_service.get_user_behavior_profile(user_id)
            if profile and profile.archetype:
                profile_label = profile.archetype.replace("_", " ").title()
                manifest_fields.append("behavior_profile")
        except Exception as e:
            logger.debug("No behavior profile available: %s", e)

        # 5. Build compact structured text
        rate_str = f"{round(savings_rate * 100, 1)}%" if savings_rate is not None else "N/A"
        context_lines = [
            "### User Financial Summary (Aggregated & Anonymized)",
            f"- Current Month Income: ৳{current_income:,.2f}",
            f"- Current Month Expenses: ৳{current_expense:,.2f}",
            f"- Current Month Savings: ৳{current_savings:,.2f} (Savings Rate: {rate_str})",
            f"- Current Unallocated Surplus: ৳{current_surplus:,.2f}",
            f"- Financial Archetype: {profile_label}",
            f"- Active Goals Count: {len(active_goals)}",
        ]

        if active_goals:
            goal_items = [
                f"{g.name}: ৳{float(g.current_amount):,.0f} / ৳{float(g.target_amount):,.0f} ({g.progress_pct:.1f}%)"
                for g in active_goals[:3]
            ]
            context_lines.append(f"- Top Active Goals: {'; '.join(goal_items)}")

        formatted_context = "\n".join(context_lines)

        data_manifest = {
            "fields_included": manifest_fields,
            "has_history": has_history,
            "active_goals_count": len(active_goals),
            "raw_transactions_included": False,
            "pii_scrubbed": True,
            "user_id_anonymized": True,
        }

        # Filter out 0.0 from grounding numbers to avoid trivial zero matches
        filtered_grounding_nums = {n for n in grounding_nums if n != 0.0}

        return UserContext(
            formatted_context=formatted_context,
            data_manifest=data_manifest,
            grounding_numbers=filtered_grounding_nums,
        )
