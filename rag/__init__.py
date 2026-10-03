"""RAG knowledge base and plain-Python semantic retrieval package."""

from __future__ import annotations

from rag.embeddings.provider import EmbeddingProvider, get_embedding_provider
from rag.ingestion.chunker import DocumentChunk, HeadingAwareChunker
from rag.ingestion.parser import ParsedDocument, parse_markdown_document
from rag.ingestion.pipeline import IngestionStats, RAGIngestionPipeline
from rag.retrieval.retriever import RAGRetriever, RetrievedPassage

__all__ = [
    "DocumentChunk",
    "EmbeddingProvider",
    "HeadingAwareChunker",
    "IngestionStats",
    "ParsedDocument",
    "RAGIngestionPipeline",
    "RAGRetriever",
    "RetrievedPassage",
    "get_embedding_provider",
    "parse_markdown_document",
]
