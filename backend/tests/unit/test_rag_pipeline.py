"""Unit and integration tests for RAG ingestion pipeline, embeddings, and retriever."""

from __future__ import annotations

import asyncio
from pathlib import Path

import numpy as np
import pytest
from rag.embeddings.provider import DeterministicLocalEmbedding, get_embedding_provider
from rag.eval.evaluate import run_rag_evaluation
from rag.ingestion.chunker import HeadingAwareChunker
from rag.ingestion.parser import parse_markdown_document
from rag.ingestion.pipeline import RAGIngestionPipeline
from rag.retrieval.retriever import RAGRetriever
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


def test_markdown_parser_extracts_frontmatter_and_content() -> None:
    """Verify parse_markdown_document extracts YAML frontmatter and body."""
    doc_path = Path("rag/documents/budgeting-50-30-20.md")
    assert doc_path.exists(), "Sample document must exist"

    parsed = parse_markdown_document(doc_path)
    assert parsed.doc_id == "budgeting-50-30-20"
    assert parsed.topic == "budgeting"
    assert parsed.language == "en"
    assert parsed.version == "1.0"
    assert "50/30/20" in parsed.title
    assert "### 50% for Needs" in parsed.body_markdown


def test_heading_aware_chunker_bounds_and_metadata() -> None:
    """Verify chunker respects heading hierarchy, token estimation, and creates valid chunks."""
    doc_path = Path("rag/documents/budgeting-50-30-20.md")
    parsed = parse_markdown_document(doc_path)

    chunker = HeadingAwareChunker(min_tokens=100, target_tokens=300, max_tokens=500)
    chunks = chunker.chunk_document(parsed)

    assert len(chunks) >= 1
    for i, chunk in enumerate(chunks):
        assert chunk.chunk_index == i
        assert chunk.doc_id == parsed.doc_id
        assert chunk.topic == parsed.topic
        assert chunk.content_hash != ""
        assert chunk.estimated_tokens > 0
        assert chunk.estimated_tokens <= 600  # Within acceptable margin


def test_deterministic_embedding_provider_properties() -> None:
    """Verify deterministic embedding provider is reproducible, unit-normalized, and 1536-dimensional."""
    provider = DeterministicLocalEmbedding(dimension=1536, seed=42)
    assert provider.dimension == 1536

    text_a = "How to build an emergency fund covering 3 to 6 months of expenses."
    text_b = "How to build an emergency fund covering 3 to 6 months of expenses."
    text_c = "High-interest credit card revolving debt and minimum payment traps."

    emb_a1 = provider.embed_text(text_a)
    emb_a2 = provider.embed_text(text_b)
    emb_c = provider.embed_text(text_c)

    # 1. Deterministic reproducibility
    assert emb_a1 == emb_a2, "Identical text must produce identical vectors"
    assert len(emb_a1) == 1536

    # 2. Unit Euclidean norm
    norm_a = np.linalg.norm(np.array(emb_a1))
    assert abs(norm_a - 1.0) < 1e-4, "Vectors must be unit normalized"

    # 3. Semantic sensitivity
    sim_identical = float(np.dot(emb_a1, emb_a2))
    sim_different = float(np.dot(emb_a1, emb_c))
    assert sim_identical > 0.99
    assert sim_identical > sim_different


@pytest.mark.asyncio
async def test_rag_ingestion_pipeline_idempotency(db_session_factory) -> None:
    """Verify pipeline ingestion is idempotent: re-running does not duplicate records."""
    provider = get_embedding_provider("deterministic")
    pipeline = RAGIngestionPipeline(
        documents_dir="rag/documents",
        embedding_provider=provider,
    )

    # First ingestion run
    async with db_session_factory() as session:
        stats_1 = await pipeline.run_db(session)
        await session.commit()

    assert stats_1.total_chunks > 0
    assert stats_1.chunks_inserted == stats_1.total_chunks
    assert stats_1.chunks_unchanged == 0

    # Verify rows in database
    async with db_session_factory() as session:
        count_res = await session.execute(select(RAGChunk))
        initial_db_rows = len(count_res.scalars().all())
    assert initial_db_rows == stats_1.total_chunks

    # Second ingestion run (idempotent re-run)
    async with db_session_factory() as session:
        stats_2 = await pipeline.run_db(session)
        await session.commit()

    assert stats_2.chunks_inserted == 0, "No new chunks should be inserted on identical re-run"
    assert stats_2.chunks_unchanged == stats_1.total_chunks
    assert stats_2.chunks_updated == 0

    # Verify row count has not duplicated
    async with db_session_factory() as session:
        count_res_2 = await session.execute(select(RAGChunk))
        final_db_rows = len(count_res_2.scalars().all())
    assert final_db_rows == initial_db_rows, "Database chunk count must remain strictly constant"


@pytest.mark.asyncio
async def test_retriever_cosine_search_and_metadata_filtering(db_session_factory) -> None:
    """Verify RAGRetriever returns top-k cosine results and respects topic filters."""
    provider = get_embedding_provider("deterministic")
    pipeline = RAGIngestionPipeline(documents_dir="rag/documents", embedding_provider=provider)

    async with db_session_factory() as session:
        await pipeline.run_db(session)
        await session.commit()

    async with db_session_factory() as session:
        retriever = RAGRetriever(session=session, embedding_provider=provider)

        # 1. Search without filters
        passages = await retriever.retrieve(
            query="What is the 50/30/20 budgeting rule?",
            top_k=4,
        )
        assert len(passages) == 4
        assert passages[0].score > 0.0
        assert any("50/30/20" in p.title for p in passages)

        # 2. Search with topic filter
        budgeting_passages = await retriever.retrieve(
            query="How should I allocate savings?",
            top_k=4,
            topic="budgeting",
        )
        assert len(budgeting_passages) > 0
        assert all(p.topic == "budgeting" for p in budgeting_passages)


@pytest.mark.asyncio
async def test_eval_suite_hit_rate_exceeds_threshold() -> None:
    """Verify evaluation set achieves hit@4 >= 0.85 acceptance criterion."""
    metrics = await run_rag_evaluation(
        eval_set_path="rag/eval/eval_set.json",
        documents_dir="rag/documents",
    )

    assert metrics.total_queries >= 40, f"Expected >= 40 queries, got {metrics.total_queries}"
    assert metrics.hit_at_4_pct >= 0.85, (
        f"Acceptance criteria violation: hit@4 was {metrics.hit_at_4_pct:.2%}, expected >= 85%"
    )
    assert metrics.no_result_rate <= 0.05, f"High no-result rate: {metrics.no_result_rate:.2%}"
    assert metrics.groundedness_pass_rate >= 0.85, (
        f"Low groundedness: {metrics.groundedness_pass_rate:.2%}"
    )


@pytest.mark.asyncio
async def test_rag_service_search_knowledge_contract(db_session_factory) -> None:
    """Verify backend RAGService search_knowledge returns expected dict schema."""
    from app.services.rag_service import RAGService

    provider = get_embedding_provider("deterministic")
    pipeline = RAGIngestionPipeline(documents_dir="rag/documents", embedding_provider=provider)

    async with db_session_factory() as session:
        await pipeline.run_db(session)
        await session.commit()

    async with db_session_factory() as session:
        service = RAGService(db_session=session, embedding_provider=provider)
        results = await service.search_knowledge(
            query="What is an emergency fund and why do I need one?",
            top_k=4,
        )

        assert len(results) == 4
        first = results[0]
        assert "chunk_id" in first
        assert "doc_id" in first
        assert "source" in first
        assert "title" in first
        assert "topic" in first
        assert "content" in first
        assert "score" in first
        assert "metadata" in first
        assert first["score"] > 0.0
