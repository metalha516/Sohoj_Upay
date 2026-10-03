"""RAG knowledge retriever supporting cosine similarity and metadata filtering."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from app.models.rag import RAGChunk
except ImportError:
    import sys

    backend_path = str(Path(__file__).resolve().parents[2] / "backend")
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    from app.models.rag import RAGChunk
from rag.embeddings.provider import EmbeddingProvider, get_embedding_provider
from rag.ingestion.chunker import DocumentChunk

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RetrievedPassage:
    """A retrieved knowledge passage with source identifiers and cosine similarity score."""

    chunk_id: int | str
    doc_id: str
    source: str
    title: str
    topic: str
    content: str
    score: float
    metadata: dict[str, Any]


class RAGRetriever:
    """Semantic vector retriever over RAG knowledge chunks with cosine similarity and filters."""

    def __init__(
        self,
        session: AsyncSession | None = None,
        embedding_provider: EmbeddingProvider | None = None,
        in_memory_catalog: list[tuple[DocumentChunk, list[float]]] | None = None,
    ) -> None:
        self.session = session
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.in_memory_catalog = in_memory_catalog or []

    @classmethod
    def from_chunks(
        cls,
        chunks_with_embeddings: list[tuple[DocumentChunk, list[float]]],
        embedding_provider: EmbeddingProvider | None = None,
    ) -> RAGRetriever:
        """Create a lightweight in-memory retriever directly from chunks and vectors."""
        return cls(
            session=None,
            embedding_provider=embedding_provider,
            in_memory_catalog=chunks_with_embeddings,
        )

    async def retrieve(
        self,
        query: str,
        top_k: int = 4,
        topic: str | None = None,
        language: str | None = None,
        min_score: float = -1.0,
    ) -> list[RetrievedPassage]:
        """Search top-k most relevant knowledge chunks using cosine similarity."""
        query = query.strip()
        if not query:
            return []

        # Generate normalized query embedding
        query_vector = self.embedding_provider.embed_text(query)

        if self.session is not None:
            return await self._retrieve_from_db(
                query_vector=query_vector,
                top_k=top_k,
                topic=topic,
                language=language,
                min_score=min_score,
            )

        return self._retrieve_from_memory(
            query_vector=query_vector,
            top_k=top_k,
            topic=topic,
            language=language,
            min_score=min_score,
        )

    async def _retrieve_from_db(
        self,
        query_vector: list[float],
        top_k: int,
        topic: str | None,
        language: str | None,
        min_score: float,
    ) -> list[RetrievedPassage]:
        """Retrieve from database session, adapting between PostgreSQL pgvector and SQLite fallback."""
        assert self.session is not None
        bind = self.session.bind
        dialect_name = bind.dialect.name if bind is not None else "sqlite"

        if dialect_name == "postgresql":
            # PostgreSQL with pgvector cosine distance operator (<=>)
            # Cosine similarity = 1 - cosine_distance
            stmt = select(
                RAGChunk,
                (1 - RAGChunk.embedding.cosine_distance(query_vector)).label("sim_score"),
            )

            # Metadata filtering using JSONB containment or extraction
            if topic:
                stmt = stmt.where(RAGChunk.metadata_["topic"].astext == topic)
            if language:
                stmt = stmt.where(RAGChunk.metadata_["language"].astext == language)

            stmt = stmt.order_by(RAGChunk.embedding.cosine_distance(query_vector)).limit(top_k)

            res = await self.session.execute(stmt)
            passages: list[RetrievedPassage] = []

            for row, score in res.all():
                if score < min_score:
                    continue
                meta = row.metadata_ or {}
                passages.append(
                    RetrievedPassage(
                        chunk_id=row.id,
                        doc_id=row.doc_id,
                        source=row.source,
                        title=row.title or "",
                        topic=str(meta.get("topic", "")),
                        content=row.chunk,
                        score=round(float(score), 4),
                        metadata=meta,
                    )
                )
            return passages

        # SQLite / in-memory DB fallback: fetch chunks and compute cosine in Python/numpy
        stmt = select(RAGChunk)
        result = await self.session.execute(stmt)
        all_db_chunks = result.scalars().all()

        candidates: list[tuple[RAGChunk, float]] = []
        q_vec = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec) or 1.0

        for row in all_db_chunks:
            meta = row.metadata_ or {}
            if topic and meta.get("topic") != topic:
                continue
            if language and meta.get("language") != language:
                continue

            if not row.embedding:
                continue

            d_vec = np.array(row.embedding, dtype=np.float32)
            d_norm = np.linalg.norm(d_vec) or 1.0
            # Dot product of normalized vectors = cosine similarity
            sim = float(np.dot(q_vec, d_vec) / (q_norm * d_norm))

            if sim >= min_score:
                candidates.append((row, sim))

        # Sort descending by similarity score
        candidates.sort(key=lambda item: item[1], reverse=True)
        top_candidates = candidates[:top_k]

        return [
            RetrievedPassage(
                chunk_id=row.id,
                doc_id=row.doc_id,
                source=row.source,
                title=row.title or "",
                topic=str((row.metadata_ or {}).get("topic", "")),
                content=row.chunk,
                score=round(sim, 4),
                metadata=row.metadata_ or {},
            )
            for row, sim in top_candidates
        ]

    def _retrieve_from_memory(
        self,
        query_vector: list[float],
        top_k: int,
        topic: str | None,
        language: str | None,
        min_score: float,
    ) -> list[RetrievedPassage]:
        """Retrieve from in-memory chunk list."""
        if not self.in_memory_catalog:
            return []

        q_vec = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec) or 1.0

        candidates: list[tuple[DocumentChunk, float]] = []

        for chunk, emb in self.in_memory_catalog:
            if topic and chunk.topic != topic:
                continue
            if language and chunk.language != language:
                continue

            d_vec = np.array(emb, dtype=np.float32)
            d_norm = np.linalg.norm(d_vec) or 1.0
            sim = float(np.dot(q_vec, d_vec) / (q_norm * d_norm))

            if sim >= min_score:
                candidates.append((chunk, sim))

        candidates.sort(key=lambda item: item[1], reverse=True)
        top_candidates = candidates[:top_k]

        return [
            RetrievedPassage(
                chunk_id=f"{chunk.doc_id}_{chunk.chunk_index}",
                doc_id=chunk.doc_id,
                source=chunk.source,
                title=chunk.title,
                topic=chunk.topic,
                content=chunk.content,
                score=round(sim, 4),
                metadata=chunk.metadata,
            )
            for chunk, sim in top_candidates
        ]
