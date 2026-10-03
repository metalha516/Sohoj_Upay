"""Deterministic financial simulation endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_simulation_service
from app.models.user import User
from app.schemas.simulation import (
    SimulateDoublingRequest,
    SimulateDoublingResponse,
    SimulateGoalRequest,
    SimulateGoalResponse,
    SimulateGrowthRequest,
    SimulateGrowthResponse,
    SimulateScenarioRequest,
    SimulateScenarioResponse,
)
from app.services.simulation_service import SimulationService

router = APIRouter(prefix="/simulate", tags=["Simulate"])


@router.post(
    "/growth",
    response_model=SimulateGrowthResponse,
    summary="Simulate compound growth and future value",
)
def simulate_growth(
    payload: SimulateGrowthRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
    sim_service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> SimulateGrowthResponse:
    """Simulate compound growth and periodic deposits using exact Financial Engine arithmetic."""
    return sim_service.simulate_growth(payload)


@router.post(
    "/goal",
    response_model=SimulateGoalResponse,
    summary="Simulate monthly savings required to hit a goal",
)
def simulate_goal(
    payload: SimulateGoalRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
    sim_service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> SimulateGoalResponse:
    """Simulate required monthly savings using exact annuity formulas."""
    return sim_service.simulate_goal(payload)


@router.post(
    "/doubling",
    response_model=SimulateDoublingResponse,
    summary="Simulate investment doubling time (Rule of 72 & exact compound)",
)
def simulate_doubling(
    payload: SimulateDoublingRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
    sim_service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> SimulateDoublingResponse:
    """Simulate investment doubling duration using logarithmic exact and Rule of 72."""
    return sim_service.simulate_doubling(payload)


@router.post(
    "/scenario",
    response_model=SimulateScenarioResponse,
    summary="Simulate comparative multi-year financial trajectory",
)
def simulate_scenario(
    payload: SimulateScenarioRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
    sim_service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> SimulateScenarioResponse:
    """Simulate comparative trajectory between baseline and modified cashflow scenarios."""
    return sim_service.simulate_scenario(payload)
