"""Financial spending anomalies endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user, get_ml_service
from app.models.user import User
from app.schemas.anomaly import (
    AnomalyResponse,
    AnomalyStatusUpdateRequest,
)
from app.services.ml_service import MLService

router = APIRouter(prefix="/anomalies", tags=["Anomalies"])


@router.get(
    "",
    response_model=list[AnomalyResponse],
    summary="List detected spending anomalies for current user",
)
async def list_anomalies(
    current_user: Annotated[User, Depends(get_current_user)],
    ml_service: Annotated[MLService, Depends(get_ml_service)],
    status_filter: Annotated[
        str | None,
        Query(alias="status", description="Filter by status (open, dismissed, confirmed)"),
    ] = None,
    scope: Annotated[
        str | None, Query(description="Filter by scope (transaction, category_month)")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Max results to return")] = 50,
) -> list[AnomalyResponse]:
    """List detected transaction or category spending anomalies."""
    return await ml_service.get_anomalies(
        user_id=current_user.id,
        status=status_filter,
        scope=scope,
        limit=limit,
    )


@router.patch(
    "/{anomaly_id}",
    response_model=AnomalyResponse,
    summary="Update feedback status on an anomaly",
)
async def update_anomaly_status(
    anomaly_id: uuid.UUID,
    payload: AnomalyStatusUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    ml_service: Annotated[MLService, Depends(get_ml_service)],
) -> AnomalyResponse:
    """Update anomaly feedback status (dismissed / confirmed).

    Returns 404 Not Found if the anomaly belongs to another tenant or does not exist.
    """
    updated = await ml_service.update_anomaly_status(
        user_id=current_user.id,
        anomaly_id=anomaly_id,
        new_status=payload.status,
    )
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Anomaly '{anomaly_id}' not found.",
        )
    return updated
