"""Transaction service coordinating ledger persistence, idempotency, and transactional outbox events."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_manager
from app.financial.rounding import round_currency
from app.models.transaction import Transaction
from app.repositories.goal_repo import GoalRepository
from app.repositories.outbox_repo import OutboxRepository
from app.repositories.transaction_repo import TransactionRepository
from app.schemas.transaction import (
    CashoutCreateRequest,
    TransactionCreateRequest,
    TransactionCursorPage,
    TransactionResponse,
    TxnType,
)


class TransactionService:
    """Service handling transaction lifecycle and atomic outbox dispatch."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.txn_repo = TransactionRepository(session)
        self.goal_repo = GoalRepository(session)
        self.outbox_repo = OutboxRepository(session)

    async def create_transaction(
        self,
        user_id: uuid.UUID,
        req: TransactionCreateRequest,
    ) -> tuple[Transaction, bool]:
        """Create a new transaction with idempotency and atomic outbox event.

        Returns tuple of (Transaction, is_new).
        """
        # 1. Idempotency Check
        if req.idempotency_key:
            existing = await self.txn_repo.get_by_idempotency_key(user_id, req.idempotency_key)
            if existing:
                return existing, False

        # 2. Goal validation (if goal_id specified)
        if req.goal_id:
            goal = await self.goal_repo.get_by_id_for_user(req.goal_id, user_id)
            if not goal:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Referenced financial goal does not exist or does not belong to you.",
                )

        # 3. Create Transaction
        now = datetime.now(UTC)
        ts = req.ts or now
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)

        txn = Transaction(
            user_id=user_id,
            amount=round_currency(req.amount),
            transaction_type=req.transaction_type.value,
            purpose=req.purpose.value if req.purpose else None,
            category=req.category,
            merchant=req.merchant,
            description=req.description,
            goal_id=req.goal_id,
            idempotency_key=req.idempotency_key,
            ts=ts,
            created_at=now,
        )
        created_txn = await self.txn_repo.create(txn)

        # 4. Atomic Outbox Event
        month_str = ts.strftime("%Y-%m-01")
        payload = {
            "user_id": str(user_id),
            "transaction_id": str(created_txn.id),
            "month": month_str,
            "amount": str(created_txn.amount),
            "transaction_type": created_txn.transaction_type,
            "purpose": created_txn.purpose,
            "category": created_txn.category,
            "ts": ts.isoformat(),
        }
        await self.outbox_repo.create_event(
            aggregate_id=created_txn.id,
            event_type="transaction.created",
            payload=payload,
        )

        # 5. Invalidate Dashboard Cache
        await cache_manager.delete_pattern(f"dashboard:{user_id}:*")

        return created_txn, True

    async def create_cashout(
        self,
        user_id: uuid.UUID,
        req: CashoutCreateRequest,
    ) -> tuple[Transaction, bool]:
        """Record an MFS cash-out transaction with mandatory purpose."""
        txn_req = TransactionCreateRequest(
            amount=req.amount,
            transaction_type=TxnType.CASH_OUT,
            purpose=req.purpose,
            category=req.category or "Cash Out",
            merchant=req.merchant,
            description=req.description,
            idempotency_key=req.idempotency_key,
            ts=req.ts,
        )
        return await self.create_transaction(user_id, txn_req)

    async def get_transaction(self, user_id: uuid.UUID, txn_id: uuid.UUID) -> Transaction:
        """Fetch single transaction by id, enforcing user ownership."""
        txn = await self.txn_repo.get_by_id_for_user(txn_id, user_id)
        if not txn:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found.",
            )
        return txn

    async def delete_transaction(self, user_id: uuid.UUID, txn_id: uuid.UUID) -> None:
        """Delete transaction, record outbox event for feature recomputation, and invalidate cache."""
        txn = await self.get_transaction(user_id, txn_id)
        month_str = txn.ts.strftime("%Y-%m-01")

        # Emit outbox event before deleting
        payload = {
            "user_id": str(user_id),
            "transaction_id": str(txn_id),
            "month": month_str,
        }
        await self.outbox_repo.create_event(
            aggregate_id=txn_id,
            event_type="transaction.deleted",
            payload=payload,
        )

        # Delete
        await self.txn_repo.delete_for_user(txn_id, user_id)

        # Invalidate cache
        await cache_manager.delete_pattern(f"dashboard:{user_id}:*")

    async def list_transactions(
        self,
        user_id: uuid.UUID,
        cursor: str | None = None,
        limit: int = 20,
        transaction_type: str | None = None,
        category: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> TransactionCursorPage:
        """List transactions for user with cursor pagination."""
        items, next_cursor, has_more = await self.txn_repo.list_cursor_for_user(
            user_id=user_id,
            cursor=cursor,
            limit=limit,
            transaction_type=transaction_type,
            category=category,
            start_date=start_date,
            end_date=end_date,
        )
        return TransactionCursorPage(
            items=[TransactionResponse.model_validate(t) for t in items],
            next_cursor=next_cursor,
            has_more=has_more,
        )
