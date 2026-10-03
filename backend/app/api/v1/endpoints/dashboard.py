"""Dashboard endpoints providing cached aggregated financial insights."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_dashboard_service
from app.models.user import User
from app.schemas.dashboard import (
    DashboardCategoriesResponse,
    DashboardMonthlyResponse,
    DashboardSummaryResponse,
)
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "",
    response_model=DashboardSummaryResponse,
    summary="User financial health dashboard summary",
)
async def get_dashboard_summary(
    current_user: Annotated[User, Depends(get_current_user)],
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
) -> DashboardSummaryResponse:
    """Retrieve primary summary card with <= 60s cache, invalidated on write operations."""
    return await dashboard_service.get_summary(current_user.id)


@router.get(
    "/monthly",
    response_model=DashboardMonthlyResponse,
    summary="Multi-month financial trends",
)
async def get_dashboard_monthly(
    current_user: Annotated[User, Depends(get_current_user)],
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
    limit: Annotated[int, Query(ge=1, le=24, description="Number of months to retrieve")] = 12,
) -> DashboardMonthlyResponse:
    """Retrieve multi-month financial time series for chart visualizations."""
    return await dashboard_service.get_monthly_history(current_user.id, limit=limit)


@router.get(
    "/categories",
    response_model=DashboardCategoriesResponse,
    summary="Category spending breakdown",
)
async def get_dashboard_categories(
    current_user: Annotated[User, Depends(get_current_user)],
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
    month: Annotated[date | None, Query(description="Target month (YYYY-MM-01)")] = None,
) -> DashboardCategoriesResponse:
    """Retrieve category spending composition and necessity vs discretionary split."""
    return await dashboard_service.get_categories(current_user.id, target_month=month)
