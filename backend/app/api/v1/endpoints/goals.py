"""Financial goals and contributions endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.deps import get_current_user, get_goal_service
from app.models.user import User
from app.schemas.goal import (
    GoalContributionCreateRequest,
    GoalContributionResponse,
    GoalCreateRequest,
    GoalResponse,
    GoalUpdateRequest,
)
from app.services.goal_service import GoalService

router = APIRouter(prefix="/goals", tags=["Goals"])


@router.post(
    "",
    response_model=GoalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new financial goal",
)
async def create_goal(
    req: GoalCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    goal_service: Annotated[GoalService, Depends(get_goal_service)],
) -> GoalResponse:
    """Create a savings target with initial contribution support."""
    return await goal_service.create_goal(current_user.id, req)


@router.get(
    "",
    response_model=list[GoalResponse],
    summary="List all financial goals for user",
)
async def list_goals(
    current_user: Annotated[User, Depends(get_current_user)],
    goal_service: Annotated[GoalService, Depends(get_goal_service)],
) -> list[GoalResponse]:
    """List goals augmented with progress, required monthly saving, ETA, and feasibility."""
    return await goal_service.list_goals(current_user.id)


@router.get(
    "/{goal_id}",
    response_model=GoalResponse,
    summary="Fetch single goal details and progress analytics",
)
async def get_goal(
    goal_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    goal_service: Annotated[GoalService, Depends(get_goal_service)],
) -> GoalResponse:
    """Retrieve details for a specific goal belonging to the authenticated user."""
    return await goal_service.get_goal(current_user.id, goal_id)


@router.patch(
    "/{goal_id}",
    response_model=GoalResponse,
    summary="Update financial goal details",
)
async def update_goal(
    goal_id: uuid.UUID,
    req: GoalUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    goal_service: Annotated[GoalService, Depends(get_goal_service)],
) -> GoalResponse:
    """Update goal attributes with strict mass-assignment prevention."""
    return await goal_service.update_goal(current_user.id, goal_id, req)


@router.delete(
    "/{goal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete a financial goal",
)
async def delete_goal(
    goal_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    goal_service: Annotated[GoalService, Depends(get_goal_service)],
) -> Response:
    """Delete a goal and invalidate dashboard cache."""
    await goal_service.delete_goal(current_user.id, goal_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{goal_id}/contributions",
    response_model=GoalContributionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Contribute savings toward a goal",
)
async def add_contribution(
    goal_id: uuid.UUID,
    req: GoalContributionCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    goal_service: Annotated[GoalService, Depends(get_goal_service)],
) -> GoalContributionResponse:
    """Allocate an amount toward a specific goal and recalculate completion progress."""
    return await goal_service.add_contribution(current_user.id, goal_id, req)


@router.get(
    "/{goal_id}/contributions",
    response_model=list[GoalContributionResponse],
    summary="List contributions for a goal",
)
async def list_contributions(
    goal_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    goal_service: Annotated[GoalService, Depends(get_goal_service)],
) -> list[GoalContributionResponse]:
    """Retrieve all historical contributions made toward a goal."""
    return await goal_service.list_contributions(current_user.id, goal_id)
