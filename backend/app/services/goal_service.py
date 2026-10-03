"""Financial goals service integrating the pure deterministic financial calculation engine."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_manager
from app.financial.engine import calculate_goal_progress
from app.financial.rounding import round_currency, round_ratio
from app.models.goal import FinancialGoal, GoalContribution
from app.repositories.feature_repo import FeatureRepository
from app.repositories.goal_repo import GoalRepository
from app.schemas.goal import (
    GoalContributionCreateRequest,
    GoalContributionResponse,
    GoalCreateRequest,
    GoalResponse,
    GoalUpdateRequest,
)


class GoalService:
    """Service orchestrating financial goals, progress metrics, and contributions."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.goal_repo = GoalRepository(session)
        self.feature_repo = FeatureRepository(session)

    async def _get_trailing_monthly_savings(self, user_id: uuid.UUID) -> Decimal:
        """Calculate trailing 3-month average savings from monthly features."""
        recent_features = await self.feature_repo.list_recent_for_user(user_id, limit=3)
        if not recent_features:
            return Decimal("0.00")
        positive_savings = [
            f.savings for f in recent_features if f.savings and f.savings > Decimal("0.00")
        ]
        if not positive_savings:
            return Decimal("0.00")
        return round_currency(sum(positive_savings) / Decimal(len(positive_savings)))

    def _augment_goal_analytics(
        self, goal: FinancialGoal, trailing_savings: Decimal
    ) -> GoalResponse:
        """Augment a raw FinancialGoal model with financial engine progress and feasibility."""
        now_date = datetime.now(UTC).date()
        target_amount = goal.target_amount
        current_amount = goal.current_amount

        # Progress calculation
        progress_pct = Decimal("1.0000")
        if target_amount > Decimal("0.00"):
            progress_pct = round_ratio(min(Decimal("1.0000"), current_amount / target_amount))

        months_remaining: int | None = None
        required_monthly: Decimal = Decimal("0.00")
        is_on_track = True
        eta: date | None = None
        feasibility_ratio: Decimal | None = None

        if goal.status == "achieved" or current_amount >= target_amount:
            is_on_track = True
            progress_pct = Decimal("1.0000")
        elif goal.target_date and goal.target_date > now_date:
            try:
                progress_res = calculate_goal_progress(
                    target=target_amount,
                    current=current_amount,
                    target_date=goal.target_date,
                    today=now_date,
                    avg_monthly_saving=trailing_savings,
                )
                months_remaining = progress_res.months_remaining
                required_monthly = progress_res.required_monthly_saving
                is_on_track = progress_res.is_on_track
                eta = progress_res.projected_completion_date
                if required_monthly > Decimal("0.00"):
                    feasibility_ratio = round_ratio(trailing_savings / required_monthly)
            except Exception:
                pass
        elif current_amount < target_amount and trailing_savings > Decimal("0.00"):
            # No target date, but projected ETA based on savings velocity
            shortfall = target_amount - current_amount
            months_needed = int((shortfall / trailing_savings).to_integral_value())
            if months_needed > 0:
                # Approximate ETA
                year_delta, month_delta = divmod(now_date.month + months_needed - 1, 12)
                eta = date(now_date.year + year_delta, month_delta + 1, 1)

        return GoalResponse(
            id=goal.id,
            user_id=goal.user_id,
            name=goal.name,
            target_amount=goal.target_amount,
            current_amount=goal.current_amount,
            target_date=goal.target_date,
            status=goal.status,
            progress_pct=progress_pct,
            months_remaining=months_remaining,
            required_monthly_saving=required_monthly,
            is_on_track=is_on_track,
            eta=eta,
            feasibility_ratio=feasibility_ratio,
            created_at=goal.created_at,
            updated_at=goal.updated_at,
        )

    async def create_goal(self, user_id: uuid.UUID, req: GoalCreateRequest) -> GoalResponse:
        """Create a new savings goal with optional initial contribution."""
        now = datetime.now(UTC)
        goal = FinancialGoal(
            user_id=user_id,
            name=req.name.strip(),
            target_amount=round_currency(req.target_amount),
            current_amount=round_currency(req.initial_amount),
            target_date=req.target_date,
            status="active",
            created_at=now,
            updated_at=now,
        )
        created_goal = await self.goal_repo.create(goal)

        if req.initial_amount > Decimal("0.00"):
            initial_contrib = GoalContribution(
                goal_id=created_goal.id,
                user_id=user_id,
                amount=round_currency(req.initial_amount),
                created_at=now,
            )
            self.session.add(initial_contrib)
            await self.session.flush()

        await cache_manager.delete_pattern(f"dashboard:{user_id}:*")
        trailing = await self._get_trailing_monthly_savings(user_id)
        return self._augment_goal_analytics(created_goal, trailing)

    async def get_goal(self, user_id: uuid.UUID, goal_id: uuid.UUID) -> GoalResponse:
        """Fetch a specific goal with progress and feasibility metrics."""
        goal = await self.goal_repo.get_by_id_for_user(goal_id, user_id)
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Financial goal not found.",
            )
        trailing = await self._get_trailing_monthly_savings(user_id)
        return self._augment_goal_analytics(goal, trailing)

    async def list_goals(self, user_id: uuid.UUID) -> list[GoalResponse]:
        """List all goals for the user augmented with calculated analytics."""
        goals = await self.goal_repo.list_all_for_user(user_id)
        trailing = await self._get_trailing_monthly_savings(user_id)
        return [self._augment_goal_analytics(g, trailing) for g in goals]

    async def update_goal(
        self,
        user_id: uuid.UUID,
        goal_id: uuid.UUID,
        req: GoalUpdateRequest,
    ) -> GoalResponse:
        """Update an existing goal and recalculate its metrics."""
        goal = await self.goal_repo.get_by_id_for_user(goal_id, user_id)
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Financial goal not found.",
            )

        if req.name is not None:
            goal.name = req.name.strip()
        if req.target_amount is not None:
            goal.target_amount = round_currency(req.target_amount)
        if req.target_date is not None:
            goal.target_date = req.target_date
        if req.status is not None:
            goal.status = req.status.value

        goal.updated_at = datetime.now(UTC)
        await self.session.flush()
        await cache_manager.delete_pattern(f"dashboard:{user_id}:*")

        trailing = await self._get_trailing_monthly_savings(user_id)
        return self._augment_goal_analytics(goal, trailing)

    async def delete_goal(self, user_id: uuid.UUID, goal_id: uuid.UUID) -> None:
        """Delete goal and invalidate user dashboard cache."""
        goal = await self.goal_repo.get_by_id_for_user(goal_id, user_id)
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Financial goal not found.",
            )
        await self.goal_repo.delete_for_user(goal_id, user_id)
        await cache_manager.delete_pattern(f"dashboard:{user_id}:*")

    async def add_contribution(
        self,
        user_id: uuid.UUID,
        goal_id: uuid.UUID,
        req: GoalContributionCreateRequest,
    ) -> GoalContributionResponse:
        """Record an explicit savings contribution toward a goal."""
        goal = await self.goal_repo.get_by_id_for_user(goal_id, user_id)
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Financial goal not found.",
            )

        contrib = GoalContribution(
            goal_id=goal_id,
            user_id=user_id,
            transaction_id=req.transaction_id,
            amount=round_currency(req.amount),
            created_at=datetime.now(UTC),
        )
        saved_contrib = await self.goal_repo.add_contribution(contrib)
        await cache_manager.delete_pattern(f"dashboard:{user_id}:*")

        return GoalContributionResponse.model_validate(saved_contrib)

    async def list_contributions(
        self, user_id: uuid.UUID, goal_id: uuid.UUID
    ) -> list[GoalContributionResponse]:
        """Fetch all contributions made toward a specific goal."""
        goal = await self.goal_repo.get_by_id_for_user(goal_id, user_id)
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Financial goal not found.",
            )
        contribs = await self.goal_repo.get_contributions_for_goal(goal_id, user_id)
        return [GoalContributionResponse.model_validate(c) for c in contribs]
