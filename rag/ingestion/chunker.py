"""Heading-aware text chunker with target token sizing and overlap."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any

from rag.ingestion.parser import ParsedDocument


@dataclass(frozen=True)
class DocumentChunk:
    """Individual chunk extracted from a parsed document."""

    doc_id: str
    source: str
    title: str
    topic: str
    language: str
    version: str
    heading: str
    chunk_index: int
    content: str
    content_hash: str
    estimated_tokens: int
    metadata: dict[str, Any]


def estimate_tokens(text: str) -> int:
    """Estimate token count for English financial text (~1.3 tokens per whitespace word)."""
    words = len(text.split())
    # Estimate roughly 1.3 tokens per word, minimum 1 token if text is non-empty
    return max(1, int(words * 1.3)) if words > 0 else 0


class HeadingAwareChunker:
    """Chunks markdown documents while respecting section headers, token limits, and overlap."""

    def __init__(
        self,
        min_tokens: int = 150,
        target_tokens: int = 380,
        max_tokens: int = 500,
        overlap_pct: float = 0.12,  # 12% overlap
    ) -> None:
        self.min_tokens = min_tokens
        self.target_tokens = target_tokens
        self.max_tokens = max_tokens
        self.overlap_pct = overlap_pct

    def chunk_document(self, doc: ParsedDocument) -> list[DocumentChunk]:
        """Split a parsed markdown document into heading-aware chunks."""
        sections = self._split_by_headings(doc.body_markdown)
        chunks: list[DocumentChunk] = []
        chunk_idx = 0

        # Accumulate sections into semantic blocks meeting target token range
        current_heading = doc.title
        current_paragraphs: list[str] = []
        current_token_count = 0

        for heading, text_block in sections:
            block_tokens = estimate_tokens(text_block)

            # If a single section is larger than max_tokens, sub-chunk it
            if block_tokens > self.max_tokens:
                # Flush existing buffer first
                if current_paragraphs:
                    combined_text = "\n\n".join(current_paragraphs).strip()
                    if combined_text:
                        chunks.append(
                            self._create_chunk(
                                doc=doc,
                                heading=current_heading,
                                chunk_index=chunk_idx,
                                content=combined_text,
                            )
                        )
                        chunk_idx += 1
                    current_paragraphs = []
                    current_token_count = 0

                sub_chunks = self._split_large_block(text_block, heading, doc)
                for sc_text in sub_chunks:
                    chunks.append(
                        self._create_chunk(
                            doc=doc,
                            heading=heading,
                            chunk_index=chunk_idx,
                            content=sc_text,
                        )
                    )
                    chunk_idx += 1
                current_heading = heading
                continue

            # Check if adding this section exceeds max_tokens
            if current_token_count + block_tokens > self.max_tokens and current_paragraphs:
                combined_text = "\n\n".join(current_paragraphs).strip()
                chunks.append(
                    self._create_chunk(
                        doc=doc,
                        heading=current_heading,
                        chunk_index=chunk_idx,
                        content=combined_text,
                    )
                )
                chunk_idx += 1

                # Calculate overlap: retain the last paragraph if its tokens are within overlap limit
                overlap_tokens_target = int(self.target_tokens * self.overlap_pct)
                overlap_paras: list[str] = []
                overlap_tokens = 0
                for p in reversed(current_paragraphs):
                    p_tok = estimate_tokens(p)
                    if overlap_tokens + p_tok <= overlap_tokens_target:
                        overlap_paras.insert(0, p)
                        overlap_tokens += p_tok
                    else:
                        break

                current_paragraphs = overlap_paras
                current_token_count = overlap_tokens

            # Append current section
            current_heading = heading if heading != doc.title else current_heading
            current_paragraphs.append(text_block)
            current_token_count += block_tokens

        # Flush remaining buffer
        if current_paragraphs:
            combined_text = "\n\n".join(current_paragraphs).strip()
            if combined_text:
                chunks.append(
                    self._create_chunk(
                        doc=doc,
                        heading=current_heading,
                        chunk_index=chunk_idx,
                        content=combined_text,
                    )
                )

        return chunks

    def _split_by_headings(self, markdown_text: str) -> list[tuple[str, str]]:
        """Split markdown by #, ##, or ### headings into (heading, text_block) tuples."""
        lines = markdown_text.splitlines()
        sections: list[tuple[str, str]] = []
        current_heading = "Overview"
        current_lines: list[str] = []

        header_regex = re.compile(r"^(#{1,3})\s+(.+)$")

        for line in lines:
            match = header_regex.match(line)
            if match:
                if current_lines:
                    text = "\n".join(current_lines).strip()
                    if text:
                        sections.append((current_heading, text))
                    current_lines = []
                current_heading = match.group(2).strip()
                current_lines.append(line)
            else:
                current_lines.append(line)

        if current_lines:
            text = "\n".join(current_lines).strip()
            if text:
                sections.append((current_heading, text))

        return sections

    def _split_large_block(self, text_block: str, heading: str, doc: ParsedDocument) -> list[str]:
        """Split an oversized block into chunks within [min_tokens, max_tokens] with overlap."""
        paragraphs = [p.strip() for p in text_block.split("\n\n") if p.strip()]
        chunks: list[str] = []
        buffer: list[str] = []
        buffer_tokens = 0

        for p in paragraphs:
            p_tokens = estimate_tokens(p)
            if buffer_tokens + p_tokens > self.max_tokens and buffer:
                chunk_str = f"## {heading}\n\n" + "\n\n".join(buffer)
                chunks.append(chunk_str)

                # Overlap: keep last paragraph
                overlap_tokens_target = int(self.target_tokens * self.overlap_pct)
                if p_tokens <= overlap_tokens_target:
                    buffer = [buffer[-1]] if buffer else []
                    buffer_tokens = estimate_tokens(buffer[0]) if buffer else 0
                else:
                    buffer = []
                    buffer_tokens = 0

            buffer.append(p)
            buffer_tokens += p_tokens

        if buffer:
            chunk_str = f"## {heading}\n\n" + "\n\n".join(buffer)
            chunks.append(chunk_str)

        return chunks

    def _create_chunk(
        self,
        doc: ParsedDocument,
        heading: str,
        chunk_index: int,
        content: str,
    ) -> DocumentChunk:
        """Construct a DocumentChunk with SHA-256 hash and metadata."""
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        tokens = estimate_tokens(content)

        meta = {
            "source": doc.source,
            "doc_id": doc.doc_id,
            "title": doc.title,
            "topic": doc.topic,
            "language": doc.language,
            "version": doc.version,
            "heading": heading,
            "chunk_index": chunk_index,
            "estimated_tokens": tokens,
        }

        return DocumentChunk(
            doc_id=doc.doc_id,
            source=doc.source,
            title=doc.title,
            topic=doc.topic,
            language=doc.language,
            version=doc.version,
            heading=heading,
            chunk_index=chunk_index,
            content=content,
            content_hash=content_hash,
            estimated_tokens=tokens,
            metadata=meta,
        )
