"""RAG ingestion pipeline for parsing, chunking, embedding, and idempotent upsert."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
from rag.ingestion.chunker import DocumentChunk, HeadingAwareChunker
from rag.ingestion.parser import parse_markdown_document

logger = logging.getLogger(__name__)


@dataclass
class IngestionStats:
    """Summary statistics for an ingestion run."""

    documents_processed: int = 0
    total_chunks: int = 0
    chunks_inserted: int = 0
    chunks_updated: int = 0
    chunks_unchanged: int = 0


class RAGIngestionPipeline:
    """Orchestrates document loading, heading-aware chunking, embedding, and idempotent storage."""

    def __init__(
        self,
        documents_dir: Path | str = "rag/documents",
        embedding_provider: EmbeddingProvider | None = None,
        chunker: HeadingAwareChunker | None = None,
    ) -> None:
        self.documents_dir = Path(documents_dir)
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.chunker = chunker or HeadingAwareChunker()

    def load_and_chunk_documents(self) -> list[DocumentChunk]:
        """Load all markdown documents in documents_dir and chunk them."""
        doc_files = sorted(self.documents_dir.glob("*.md"))
        all_chunks: list[DocumentChunk] = []

        for f in doc_files:
            parsed = parse_markdown_document(f)
            chunks = self.chunker.chunk_document(parsed)
            all_chunks.extend(chunks)

        logger.info(
            "Parsed %d documents into %d chunks from %s",
            len(doc_files),
            len(all_chunks),
            self.documents_dir,
        )
        return all_chunks

    def embed_chunks(self, chunks: list[DocumentChunk]) -> list[tuple[DocumentChunk, list[float]]]:
        """Generate embedding vectors for all document chunks."""
        texts = [c.content for c in chunks]
        embeddings = self.embedding_provider.embed_batch(texts)
        return list(zip(chunks, embeddings, strict=True))

    async def run_db(self, session: AsyncSession) -> IngestionStats:
        """Execute the ingestion pipeline and idempotently upsert into rag_chunks table.

        Idempotency Guarantee:
        - Matches existing records by (doc_id, chunk_index).
        - If content_hash matches existing metadata, row is unchanged (no-op).
        - If content_hash differs, updates text and vector.
        - Deletes orphaned chunks if document was updated with fewer chunks.
        """
        stats = IngestionStats()
        doc_files = sorted(self.documents_dir.glob("*.md"))
        stats.documents_processed = len(doc_files)

        all_chunks = self.load_and_chunk_documents()
        stats.total_chunks = len(all_chunks)

        if not all_chunks:
            return stats

        # Generate embeddings
        chunk_embeddings = self.embed_chunks(all_chunks)

        # Process per doc_id for clean transaction handling and orphan removal
        doc_ids = {c.doc_id for c in all_chunks}

        for current_doc_id in doc_ids:
            # Query existing chunks for this doc_id
            stmt = select(RAGChunk).where(RAGChunk.doc_id == current_doc_id)
            result = await session.execute(stmt)
            existing_chunks = {
                (row.metadata_.get("chunk_index") if row.metadata_ else None): row
                for row in result.scalars().all()
            }

            current_doc_chunks = [
                (c, emb) for (c, emb) in chunk_embeddings if c.doc_id == current_doc_id
            ]
            active_indices: set[int] = set()

            for chunk, emb in current_doc_chunks:
                active_indices.add(chunk.chunk_index)
                existing = existing_chunks.get(chunk.chunk_index)

                metadata_payload: dict[str, Any] = {
                    **chunk.metadata,
                    "content_hash": chunk.content_hash,
                }

                if existing is not None:
                    # Compare content hash
                    existing_hash = (
                        existing.metadata_.get("content_hash") if existing.metadata_ else None
                    )
                    if existing_hash == chunk.content_hash:
                        stats.chunks_unchanged += 1
                        continue

                    # Update changed chunk
                    existing.title = chunk.title
                    existing.source = chunk.source
                    existing.chunk = chunk.content
                    existing.embedding = emb
                    existing.metadata_ = metadata_payload
                    stats.chunks_updated += 1
                else:
                    # Insert new chunk
                    new_entity = RAGChunk(
                        doc_id=chunk.doc_id,
                        source=chunk.source,
                        title=chunk.title,
                        chunk=chunk.content,
                        embedding=emb,
                        metadata_=metadata_payload,
                    )
                    session.add(new_entity)
                    stats.chunks_inserted += 1

            # Remove obsolete chunks if document shrunk
            for old_idx, old_chunk in existing_chunks.items():
                if old_idx not in active_indices and old_idx is not None:
                    await session.delete(old_chunk)

        await session.flush()
        return stats
