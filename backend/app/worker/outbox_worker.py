"""Transactional outbox worker processing asynchronous ML feature recomputation and cache invalidation."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_manager
from app.core.config import get_settings
from app.db.session import get_session_factory
from app.ml.features import MonthlyFeatureEngine
from app.models.outbox import OutboxEvent
from app.models.transaction import Transaction
from app.repositories.feature_repo import FeatureRepository
from app.repositories.outbox_repo import OutboxRepository

logger = logging.getLogger("app.worker.outbox")


async def process_single_outbox_event(session: AsyncSession, event: OutboxEvent) -> dict[str, Any]:
    """Process a single outbox event, recomputing features and updating cache."""
    user_id_str = event.payload.get("user_id")
    if not user_id_str:
        logger.warning("Outbox event %s missing user_id in payload", event.id)
        event.processed_at = datetime.now(UTC)
        await session.flush()
        return {"status": "skipped", "reason": "missing_user_id"}

    user_id = uuid.UUID(user_id_str)
    feature_repo = FeatureRepository(session)

    # 1. Fetch all user transactions to compute features
    txn_stmt = (
        select(Transaction).where(Transaction.user_id == user_id).order_by(Transaction.ts.asc())
    )
    txn_res = await session.execute(txn_stmt)
    txns = txn_res.scalars().all()

    # Convert to dict representation for MonthlyFeatureEngine
    txn_dicts: list[dict[str, Any]] = [
        {
            "id": t.id,
            "user_id": t.user_id,
            "amount": t.amount,
            "transaction_type": t.transaction_type,
            "purpose": t.purpose,
            "category": t.category,
            "ts": t.ts,
            "created_at": t.created_at,
        }
        for t in txns
    ]

    # 2. Recompute monthly features using shared engine
    engine = MonthlyFeatureEngine()
    feature_records = engine.compute_user_features(user_id, txn_dicts)

    # 3. Upsert features into monthly_features table
    for record in feature_records:
        await feature_repo.upsert_feature(
            user_id=user_id,
            month=record.month,
            data=record.model_dump(),
        )

    # 4. Invalidate dashboard cache
    await cache_manager.delete_pattern(f"dashboard:{user_id}:*")

    # 5. Anomaly Pipeline: evaluate transaction against Model B and persist anomaly + recommendation
    if event.event_type in ("transaction.created", "transaction_created") and event.payload:
        payload = event.payload
        txn_id_str = payload.get("id") or payload.get("transaction_id")
        txn_id = uuid.UUID(txn_id_str) if txn_id_str else None
        amt_str = payload.get("amount")
        cat = payload.get("category", "other")
        if amt_str:
            try:
                from app.services.ml_service import MLService

                ml_service = MLService(session)
                await ml_service.evaluate_transaction_anomaly(
                    user_id=user_id,
                    txn_id=txn_id,
                    amount=Decimal(str(amt_str)),
                    category=cat,
                )
            except Exception as e:
                logger.warning("Anomaly evaluation failed for transaction %s: %s", txn_id, e)

    logger.info(
        "Outbox event %s processed: updated %d monthly features for user %s",
        event.id,
        len(feature_records),
        user_id,
    )

    # 6. Mark processed
    event.processed_at = datetime.now(UTC)
    await session.flush()

    return {
        "status": "success",
        "event_id": event.id,
        "features_updated": len(feature_records),
    }


async def drain_outbox(session: AsyncSession, batch_size: int = 50) -> int:
    """Drain and process pending events from the outbox table."""
    outbox_repo = OutboxRepository(session)
    events = await outbox_repo.get_unprocessed_events(limit=batch_size)

    count = 0
    for event in events:
        try:
            await process_single_outbox_event(session, event)
            await session.commit()
            count += 1
        except Exception as exc:
            logger.error("Failed to process outbox event %s: %s", event.id, exc, exc_info=True)
            await session.rollback()

    return count


async def run_worker_drain_cycle() -> int:
    """Standalone worker loop execution using the application session factory."""
    factory = get_session_factory()
    async with factory() as session:
        return await drain_outbox(session)


# -----------------------------------------------------------------------------
# Arq Worker Settings
# -----------------------------------------------------------------------------

try:
    from arq.connections import RedisSettings

    async def arq_drain_outbox_task(ctx: dict[str, Any]) -> int:
        """Arq background task executing an outbox drain cycle."""
        return await run_worker_drain_cycle()

    class WorkerSettings:
        """Arq worker configuration."""

        functions = [arq_drain_outbox_task]
        redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
        max_jobs = 10
        poll_delay = 0.5

except ImportError:
    pass
