"""Security, privacy, and content compliance tests for RAG knowledge base."""

from __future__ import annotations

import asyncio
import re
from pathlib import Path

import pytest
from rag.embeddings.provider import get_embedding_provider
from rag.ingestion.pipeline import RAGIngestionPipeline
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base
from app.models.rag import RAGChunk


@pytest.fixture
def db_session_factory():
    """Create an in-memory SQLite async session factory."""
    test_db_url = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(test_db_url, future=True)
    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )

    async def _init_models() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_init_models())
    yield session_factory
    asyncio.run(engine.dispose())


@pytest.mark.asyncio
async def test_no_user_transactions_or_pii_in_rag_chunks(db_session_factory) -> None:
    """Guarantee that no user transactions, account balances, or PII ever enter rag_chunks.

    Security standard: RAG knowledge base is strictly public educational material.
    """
    provider = get_embedding_provider("deterministic")
    pipeline = RAGIngestionPipeline(
        documents_dir="rag/documents",
        embedding_provider=provider,
    )

    async with db_session_factory() as session:
        await pipeline.run_db(session)
        await session.commit()

    # Scan every chunk in rag_chunks
    async with db_session_factory() as session:
        res = await session.execute(select(RAGChunk))
        chunks = res.scalars().all()

    assert len(chunks) > 0, "Ingestion must have loaded chunks"

    # Regex patterns for PII
    email_regex = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
    phone_bd_regex = re.compile(r"(?:\+?88)?01[3-9]\d{8}")
    uuid_regex = re.compile(
        r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I
    )
    pii_keywords = ["password_hash", "argon2id", "refresh_token", "access_token", "secret_key"]

    valid_sources = {p.name for p in Path("rag/documents").glob("*.md")}

    for row in chunks:
        text = row.chunk.lower()

        # 1. Source must be a known educational document
        assert row.source in valid_sources, f"Unauthorized source in RAG: {row.source}"

        # 2. No email addresses
        assert not email_regex.search(row.chunk), f"Email detected in chunk {row.id}"

        # 3. No phone numbers
        assert not phone_bd_regex.search(row.chunk), f"Phone number detected in chunk {row.id}"

        # 4. No UUIDs (guarantees no user_id, transaction_id, or goal_id leaks)
        assert not uuid_regex.search(row.chunk), f"UUID identifier detected in chunk {row.id}"

        # 5. No sensitive authentication keys
        for kw in pii_keywords:
            assert kw not in text, f"Sensitive keyword '{kw}' found in chunk {row.id}"

        # 6. Metadata verification
        meta = row.metadata_ or {}
        assert "user_id" not in meta, f"user_id found in metadata for chunk {row.id}"
        assert "transaction_id" not in meta, f"transaction_id found in metadata for chunk {row.id}"


def test_corpus_content_reviewed_for_prohibited_guaranteed_returns() -> None:
    """Content review: verify absence of 'guaranteed returns' or risk-free investment claims.

    Compliance rule: Educational financial content must never promise guaranteed profits.
    """
    doc_files = list(Path("rag/documents").glob("*.md"))
    assert len(doc_files) >= 40, f"Expected >= 40 documents, found {len(doc_files)}"

    prohibited_patterns = [
        re.compile(r"\bguaranteed return\b", re.I),
        re.compile(r"\bguaranteed returns\b", re.I),
        re.compile(r"\brisk-free profit\b", re.I),
        re.compile(r"\brisk-free return\b", re.I),
        re.compile(r"\bguaranteed profit\b", re.I),
        re.compile(r"\bguaranteed wealth\b", re.I),
        re.compile(r"\brisk-free investment\b", re.I),
        re.compile(r"\b100% safe profit\b", re.I),
    ]

    violations: list[str] = []

    for f in doc_files:
        content = f.read_text(encoding="utf-8")
        for pat in prohibited_patterns:
            if pat.search(content):
                violations.append(f"{f.name}: matched prohibited pattern '{pat.pattern}'")

    assert not violations, "Prohibited investment claims found in corpus:\n" + "\n".join(violations)
