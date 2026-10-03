# RAG Knowledge Corpus & Ingestion

Educational financial knowledge base and plain-Python RAG retrieval engine over pgvector.

## Principles
- Holds ONLY verified, public, educational financial literacy material (savings methods, debt management, MFS tariffs, inflation context).
- Strictly NEVER stores private user transaction data or PII.
- Grounded citations returned alongside LLM responses.

## Structure
- `documents/`: Markdown and structured educational corpus.
- `ingestion/`: Chunking and text normalization scripts.
- `embeddings/`: Vector embedding generation utilities.
- `retrieval/`: Cosine similarity search and filtering logic against pgvector.
