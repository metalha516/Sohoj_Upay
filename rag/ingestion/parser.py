"""Document parser for markdown documents with YAML front-matter."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ParsedDocument:
    """Parsed markdown document with extracted metadata."""

    doc_id: str
    source: str
    title: str
    topic: str
    language: str
    version: str
    raw_content: str
    body_markdown: str
    metadata: dict[str, Any]


def parse_markdown_document(filepath: Path | str) -> ParsedDocument:
    """Read and parse a markdown document with YAML front-matter."""
    path = Path(filepath)
    raw = path.read_text(encoding="utf-8")
    doc_id = path.stem
    source = path.name

    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            frontmatter_raw = parts[1].strip()
            body_markdown = parts[2].strip()
            try:
                meta = yaml.safe_load(frontmatter_raw) or {}
            except Exception:
                meta = {}
        else:
            meta = {}
            body_markdown = raw.strip()
    else:
        meta = {}
        body_markdown = raw.strip()

    title = str(meta.get("title", doc_id.replace("-", " ").title()))
    topic = str(meta.get("topic", "general"))
    language = str(meta.get("language", "en"))
    version = str(meta.get("version", "1.0"))

    return ParsedDocument(
        doc_id=doc_id,
        source=source,
        title=title,
        topic=topic,
        language=language,
        version=version,
        raw_content=raw,
        body_markdown=body_markdown,
        metadata=meta,
    )
