"""Transaction repository."""

import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction
from app.repositories.base import BaseRepository


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

    async def create(self, transaction: Transaction) -> Transaction:
        """Persist a new transaction record."""
        self.session.add(transaction)
        await self.session.flush()
        return transaction
