"""Financial goals repository."""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.goal import FinancialGoal, GoalContribution
from app.repositories.base import BaseRepository


class GoalRepository(BaseRepository[FinancialGoal]):
    """Repository for user goals and contribution tracking."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(FinancialGoal, session)

    async def list_active_for_user(self, user_id: uuid.UUID) -> Sequence[FinancialGoal]:
        """List active financial goals for the user."""
        query = (
            select(FinancialGoal)
            .where(
                FinancialGoal.user_id == user_id,
                FinancialGoal.status == "active",
            )
            .order_by(FinancialGoal.created_at.desc())
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def add_contribution(self, contribution: GoalContribution) -> GoalContribution:
        """Add contribution and update goal current amount."""
        self.session.add(contribution)
        # Update goal current amount
        goal = await self.get_by_id_for_user(contribution.goal_id, contribution.user_id)
        if goal:
            goal.current_amount += contribution.amount
            if goal.current_amount >= goal.target_amount:
                goal.status = "achieved"
        await self.session.flush()
        return contribution
