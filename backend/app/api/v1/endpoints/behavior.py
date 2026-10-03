"""Behavioral profiling and coaching insights endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_ml_service
from app.models.user import User
from app.schemas.behavior import (
    BehaviorInsightsResponse,
    BehaviorProfileResponse,
)
from app.services.ml_service import MLService

router = APIRouter(prefix="/behavior", tags=["Behavior"])


@router.get(
    "/profile",
    response_model=BehaviorProfileResponse,
    summary="Get or refresh user behavioral archetype profile",
)
async def get_behavior_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    ml_service: Annotated[MLService, Depends(get_ml_service)],
    force: Annotated[bool, Query(description="Force recomputation bypassing debounce")] = False,
    allow_cold_start: Annotated[
        bool, Query(description="Return cold-start profile instead of INSUFFICIENT_DATA error")
    ] = False,
) -> BehaviorProfileResponse:
    """Retrieve behavioral classification profile with debounce cache and cold-start detection."""
    return await ml_service.get_or_refresh_behavior_profile(
        user_id=current_user.id,
        force=force,
        allow_cold_start=allow_cold_start,
    )


@router.get(
    "/insights",
    response_model=BehaviorInsightsResponse,
    summary="Get behavioral insights and grounded recommendations",
)
async def get_behavior_insights(
    current_user: Annotated[User, Depends(get_current_user)],
    ml_service: Annotated[MLService, Depends(get_ml_service)],
    allow_cold_start: Annotated[
        bool,
        Query(description="Allow cold-start onboarding tips instead of INSUFFICIENT_DATA error"),
    ] = False,
) -> BehaviorInsightsResponse:
    """Retrieve actionable, non-judgmental financial coaching insights based on user profile."""
    return await ml_service.get_behavior_insights(
        user_id=current_user.id,
        allow_cold_start=allow_cold_start,
    )
