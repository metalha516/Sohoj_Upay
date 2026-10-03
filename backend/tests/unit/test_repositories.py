"""Unit tests for repository ownership filtering and query composition."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import select

from app.models.goal import FinancialGoal, GoalContribution
from app.models.transaction import Transaction
from app.models.user import User
from app.repositories.audit_repo import AuditLogRepository
from app.repositories.base import BaseRepository
from app.repositories.goal_repo import GoalRepository
from app.repositories.user_repo import UserRepository


def test_base_repository_ownership_filtering() -> None:
    """Verify that _apply_ownership_filter appends WHERE user_id == :user_id to queries."""
    mock_session = AsyncMock()
    repo = BaseRepository(Transaction, mock_session)
    user_id = uuid.uuid4()

    base_query = select(Transaction)
    filtered_query = repo._apply_ownership_filter(base_query, user_id)

    # Compile query to inspect WHERE clause (hex UUID without dashes)
    compiled_str = str(filtered_query.compile(compile_kwargs={"literal_binds": True}))
    assert f"transactions.user_id = '{user_id.hex}'" in compiled_str


def test_user_repository_ownership_filtering() -> None:
    """Verify that User entity is filtered by id == :user_id."""
    mock_session = AsyncMock()
    repo = UserRepository(mock_session)
    user_id = uuid.uuid4()

    base_query = select(User)
    filtered_query = repo._apply_ownership_filter(base_query, user_id)

    compiled_str = str(filtered_query.compile(compile_kwargs={"literal_binds": True}))
    assert f"users.id = '{user_id.hex}'" in compiled_str


@pytest.mark.asyncio
async def test_audit_log_repository_is_append_only() -> None:
    """Verify that AuditLogRepository only provides append operations without update/delete."""
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    audit_repo = AuditLogRepository(mock_session)

    # Verify no update or delete methods exist on the repository
    assert not hasattr(audit_repo, "update")
    assert not hasattr(audit_repo, "delete")
    assert hasattr(audit_repo, "log_event")

    user_id = uuid.uuid4()
    entry = await audit_repo.log_event(
        actor="system",
        action="AUTH_LOGIN_SUCCESS",
        user_id=user_id,
        ip="192.168.1.1",
        metadata={"user_agent": "Mozilla/5.0"},
    )

    assert entry.actor == "system"
    assert entry.action == "AUTH_LOGIN_SUCCESS"
    assert entry.user_id == user_id
    mock_session.add.assert_called_once_with(entry)
    mock_session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_goal_repository_contribution_increments_goal() -> None:
    """Verify that adding a contribution updates goal current_amount and marks status achieved."""
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    goal_repo = GoalRepository(mock_session)
    user_id = uuid.uuid4()
    goal_id = uuid.uuid4()

    goal = FinancialGoal(
        id=goal_id,
        user_id=user_id,
        name="Emergency Reserve",
        target_amount=10000,
        current_amount=8000,
        status="active",
    )

    # Mock get_by_id_for_user to return this goal
    goal_repo.get_by_id_for_user = AsyncMock(return_value=goal)  # type: ignore[method-assign]

    contrib = GoalContribution(
        id=uuid.uuid4(),
        goal_id=goal_id,
        user_id=user_id,
        amount=2500,
    )

    await goal_repo.add_contribution(contrib)

    assert goal.current_amount == 10500
    assert goal.status == "achieved"
    mock_session.flush.assert_awaited_once()
