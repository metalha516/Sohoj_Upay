"""Transaction repository with cursor-based pagination and ownership filtering."""

from __future__ import annotations

import base64
import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction
from app.repositories.base import BaseRepository


def _encode_cursor(ts: datetime, entity_id: uuid.UUID) -> str:
    """Encode timestamp and UUID into an opaque base64 pagination cursor."""
    raw = f"{ts.isoformat()}|{entity_id}"
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8")


def _decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID] | None:
    """Decode an opaque base64 pagination cursor back to timestamp and UUID."""
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
        ts_str, id_str = raw.split("|")
        return datetime.fromisoformat(ts_str), uuid.UUID(id_str)
    except Exception:
        return None


class TransactionRepository(BaseRepository[Transaction]):
    """Repository for financial transaction operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Transaction, session)

    async def get_by_idempotency_key(
        self, user_id: uuid.UUID, idempotency_key: str
    ) -> Transaction | None:
        """Fetch transaction by idempotency key for duplicate request prevention."""
        query = select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.idempotency_key == idempotency_key,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_by_date_range(
        self,
        user_id: uuid.UUID,
        start_ts: datetime,
        end_ts: datetime,
    ) -> Sequence[Transaction]:
        """Fetch all user transactions within a specific timestamp window."""
        query = (
            select(Transaction)
            .where(
                Transaction.user_id == user_id,
                Transaction.ts >= start_ts,
                Transaction.ts <= end_ts,
            )
            .order_by(Transaction.ts.desc())
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def list_cursor_for_user(
        self,
        user_id: uuid.UUID,
        cursor: str | None = None,
        limit: int = 20,
        transaction_type: str | None = None,
        category: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> tuple[list[Transaction], str | None, bool]:
        """Fetch transactions with deterministic cursor pagination and optional filters."""
        query = select(Transaction).where(Transaction.user_id == user_id)

        if transaction_type:
            query = query.where(Transaction.transaction_type == transaction_type)
        if category:
            query = query.where(Transaction.category == category)
        if start_date:
            query = query.where(Transaction.ts >= start_date)
        if end_date:
            query = query.where(Transaction.ts <= end_date)

        if cursor:
            decoded = _decode_cursor(cursor)
            if decoded:
                cursor_ts, cursor_id = decoded
                query = query.where(
                    or_(
                        Transaction.ts < cursor_ts,
                        and_(Transaction.ts == cursor_ts, Transaction.id < cursor_id),
                    )
                )

        query = query.order_by(Transaction.ts.desc(), Transaction.id.desc()).limit(limit + 1)
        result = await self.session.execute(query)
        rows = list(result.scalars().all())

        has_more = len(rows) > limit
        items = rows[:limit]
        next_cursor = None
        if has_more and items:
            last = items[-1]
            next_cursor = _encode_cursor(last.ts, last.id)

        return items, next_cursor, has_more

    async def create(self, transaction: Transaction) -> Transaction:
        """Persist a new transaction record."""
        self.session.add(transaction)
        await self.session.flush()
        return transaction
