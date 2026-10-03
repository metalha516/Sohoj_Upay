"""Expense and savings forecasting endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_ml_service
from app.models.user import User
from app.schemas.forecast import (
    ExpenseForecastResponse,
    SavingsForecastResponse,
)
from app.core.config import get_settings
from app.services.ml_service import MLService

router = APIRouter(prefix="/forecast", tags=["Forecast"])


@router.get(
    "/expenses",
    response_model=ExpenseForecastResponse,
    summary="Forecast next-month expense with uncertainty bounds",
)
async def forecast_expenses(
    current_user: Annotated[User, Depends(get_current_user)],
    ml_service: Annotated[MLService, Depends(get_ml_service)],
    allow_cold_start: Annotated[
        bool, Query(description="Allow fallback baseline forecast during cold start")
    ] = False,
) -> ExpenseForecastResponse:
    """Predict next-month total expenses at 10th, 50th, and 90th percentiles using Model C."""
    settings = get_settings()
    if not settings.forecast_enabled:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Financial forecasting services are currently disabled by administrator.",
        )

    return await ml_service.get_expense_forecast(
        user_id=current_user.id,
        allow_cold_start=allow_cold_start,
    )


@router.get(
    "/savings",
    response_model=SavingsForecastResponse,
    summary="Forecast next-month savings capacity",
)
async def forecast_savings(
    current_user: Annotated[User, Depends(get_current_user)],
    ml_service: Annotated[MLService, Depends(get_ml_service)],
    allow_cold_start: Annotated[
        bool, Query(description="Allow fallback baseline forecast during cold start")
    ] = False,
) -> SavingsForecastResponse:
    """Predict next-month savings surplus derived from projected income and expenses."""
    settings = get_settings()
    if not settings.forecast_enabled:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Financial forecasting services are currently disabled by administrator.",
        )

    return await ml_service.get_savings_forecast(
        user_id=current_user.id,
        allow_cold_start=allow_cold_start,
    )
