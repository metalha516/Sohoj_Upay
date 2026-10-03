"""RAG Knowledge Service providing semantic retrieval for financial education."""

from __future__ import annotations

import logging
from typing import Any

from rag.embeddings.provider import EmbeddingProvider, get_embedding_provider
from rag.retrieval.retriever import RAGRetriever, RetrievedPassage
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class RAGService:
    """Service wrapping RAG knowledge retrieval over pgvector and in-memory fallback."""

    def __init__(
        self,
        db_session: AsyncSession | None = None,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        self._db_session = db_session
        self._embedding_provider = embedding_provider or get_embedding_provider()
        self._retriever = RAGRetriever(
            session=db_session,
            embedding_provider=self._embedding_provider,
        )

    async def search_knowledge(
        self,
        query: str,
        top_k: int = 4,
        topic: str | None = None,
        language: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve top-k relevant financial knowledge passages.

        Returns compact dictionaries containing doc_id, source, title, content snippet, and score.
        Strictly contains only verified educational documents; zero user transaction data or PII.
        """
        passages: list[RetrievedPassage] = await self._retriever.retrieve(
            query=query,
            top_k=top_k,
            topic=topic,
            language=language,
        )

        return [
            {
                "chunk_id": p.chunk_id,
                "doc_id": p.doc_id,
                "source": p.source,
                "title": p.title,
                "topic": p.topic,
                "content": p.content,
                "score": p.score,
                "metadata": p.metadata,
            }
            for p in passages
        ]
