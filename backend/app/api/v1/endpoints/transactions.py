"""Transaction and Cash-out endpoints per data-contract.md §1."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, Response, status

from app.api.deps import get_current_user, get_transaction_service
from app.models.user import User
from app.schemas.transaction import (
    CashoutCreateRequest,
    TransactionCreateRequest,
    TransactionCursorPage,
    TransactionResponse,
)
from app.services.transaction_service import TransactionService

router = APIRouter(tags=["Transactions"])


@router.post(
    "/transactions",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a financial transaction",
)
async def create_transaction(
    req: TransactionCreateRequest,
    response: Response,
    current_user: Annotated[User, Depends(get_current_user)],
    txn_service: Annotated[TransactionService, Depends(get_transaction_service)],
    idempotency_header: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> TransactionResponse:
    """Record a transaction with strict Decimal validation and atomic outbox dispatch."""
    if idempotency_header and not req.idempotency_key:
        req.idempotency_key = idempotency_header

    txn, is_new = await txn_service.create_transaction(current_user.id, req)
    if not is_new:
        response.status_code = status.HTTP_200_OK

    return TransactionResponse.model_validate(txn)


@router.get(
    "/transactions",
    response_model=TransactionCursorPage,
    summary="List transactions with cursor pagination",
)
async def list_transactions(
    current_user: Annotated[User, Depends(get_current_user)],
    txn_service: Annotated[TransactionService, Depends(get_transaction_service)],
    cursor: Annotated[str | None, Query(description="Pagination cursor")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    transaction_type: Annotated[str | None, Query(description="Filter by type")] = None,
    category: Annotated[str | None, Query(description="Filter by category")] = None,
    start_date: Annotated[datetime | None, Query(description="Filter start timestamp")] = None,
    end_date: Annotated[datetime | None, Query(description="Filter end timestamp")] = None,
) -> TransactionCursorPage:
    """Retrieve chronologically ordered transactions using deterministic cursor pagination."""
    return await txn_service.list_transactions(
        user_id=current_user.id,
        cursor=cursor,
        limit=limit,
        transaction_type=transaction_type,
        category=category,
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "/transactions/{transaction_id}",
    response_model=TransactionResponse,
    summary="Fetch a single transaction by ID",
)
async def get_transaction(
    transaction_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    txn_service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> TransactionResponse:
    """Retrieve details for a single transaction owned by the authenticated user."""
    txn = await txn_service.get_transaction(current_user.id, transaction_id)
    return TransactionResponse.model_validate(txn)


@router.delete(
    "/transactions/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete a transaction",
)
async def delete_transaction(
    transaction_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    txn_service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> Response:
    """Delete a transaction, triggering feature recomputation and cache invalidation."""
    await txn_service.delete_transaction(current_user.id, transaction_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# -----------------------------------------------------------------------------
# Dedicated Cash-out Endpoints
# -----------------------------------------------------------------------------


@router.post(
    "/cashouts",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record an MFS cash-out transaction",
)
async def create_cashout(
    req: CashoutCreateRequest,
    response: Response,
    current_user: Annotated[User, Depends(get_current_user)],
    txn_service: Annotated[TransactionService, Depends(get_transaction_service)],
    idempotency_header: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> TransactionResponse:
    """Record an MFS cash-out transaction with strictly mandatory spending purpose."""
    if idempotency_header and not req.idempotency_key:
        req.idempotency_key = idempotency_header

    txn, is_new = await txn_service.create_cashout(current_user.id, req)
    if not is_new:
        response.status_code = status.HTTP_200_OK

    return TransactionResponse.model_validate(txn)


@router.get(
    "/cashouts",
    response_model=TransactionCursorPage,
    summary="List cash-outs for current user",
)
async def list_cashouts(
    current_user: Annotated[User, Depends(get_current_user)],
    txn_service: Annotated[TransactionService, Depends(get_transaction_service)],
    cursor: Annotated[str | None, Query(description="Pagination cursor")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> TransactionCursorPage:
    """List cash-out transactions for current user."""
    return await txn_service.list_transactions(
        user_id=current_user.id,
        cursor=cursor,
        limit=limit,
        transaction_type="cash_out",
    )
