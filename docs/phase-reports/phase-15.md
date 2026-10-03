# Phase 15 Report: RAG Knowledge Base

## Executive Summary
Phase 15 implements an isolated, grounded financial-literacy Retrieval-Augmented Generation (RAG) knowledge engine for Sohoj. The knowledge base is authoritatively grounded in curated educational financial concepts—completely separated from private user transactions and sensitive personal identifiable information (PII). The system includes 54 original agent-authored documents, a heading-aware chunking pipeline, a provider-agnostic embedding abstraction with deterministic local evaluation, an idempotent database upsert mechanism, a semantic vector retriever supporting cosine similarity and metadata filters, and a rigorous 54-item evaluation benchmark achieving **100% hit@4** (well above the $\ge 85\%$ acceptance threshold).

---

## 1. System Architecture & Boundaries

```
+----------------------------------------------------------------------------------------------------+
|                                    Educational Knowledge Domain                                    |
|                                                                                                    |
|  rag/documents/ (54 Curated Markdown Docs with YAML Frontmatter)                                   |
|  - Budgeting (50/30/20, Zero-based, Envelopes, Irregular Income)                                  |
|  - Emergency Fund (Sizing, Storage, Boundary Rules, Rebuilding)                                   |
|  - Saving vs. Investing (Risk/Return, Horizons, Opportunity Cost)                                  |
|  - Compound Interest (Mechanics, Frequencies, Rule of 72, Real Return)                             |
|  - Inflation (Basics, CPI, Real Interest Rates, Hedging)                                           |
|  - Banking Products (DPS, FDR, Savings Accounts, Premature Encashment, Laddering)                  |
|  - Debt Strategies (Avalanche, Snowball, Good vs Bad Debt, DTI Ratio)                              |
|  - Spending Habits (24h Rule, Emotional Triggers, MFS Friction, Needs vs Wants)                    |
|  - App Guide & FAQs (KPIs, Savings Rate, Anomaly Alerts, Archetypes, Forecasts, MFS Tariffs, Security)|
|  - Glossary (Financial & Behavioral Concepts)                                                      |
+-------------------------------------------------+--------------------------------------------------+
                                                  |
                                                  v
+----------------------------------------------------------------------------------------------------+
|                                      RAG Ingestion Pipeline                                        |
|  1. parse_markdown_document() -> extracts title, topic, language, version                         |
|  2. HeadingAwareChunker()      -> 300-500 tokens, 10-15% overlap, heading hierarchy preservation   |
|  3. DeterministicLocalEmbedding() / OpenAI -> 1536-dim unit-normalized vectors                     |
|  4. Idempotent Upsert Engine   -> matches (doc_id, chunk_index) + SHA-256 hash                     |
+-------------------------------------------------+--------------------------------------------------+
                                                  |
                                                  v
+----------------------------------------------------------------------------------------------------+
|                                    PostgreSQL / SQLite Storage                                     |
|  rag_chunks table:                                                                                 |
|  - id: BIGINT PRIMARY KEY                                                                          |
|  - doc_id: VARCHAR(100), source: VARCHAR(255), title: VARCHAR(255)                                 |
|  - chunk: TEXT, embedding: vector(1536), metadata: JSONB                                           |
|                                                                                                    |
|  *** STRICT SECURITY BOUNDARY: No user transactions, accounts, balances, or PII ever stored ***    |
+-------------------------------------------------+--------------------------------------------------+
                                                  |
                                                  v
+----------------------------------------------------------------------------------------------------+
|                                   Retrieval & Service Interface                                    |
|  RAGRetriever (pgvector <=> cosine distance / SQLite numpy dot product)                            |
|  RAGService.search_knowledge(query, top_k=4, topic=None, language=None)                            |
|  Returns: [{chunk_id, doc_id, source, title, topic, content, score, metadata}]                     |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Ingestion Pipeline & Chunker Specifications

### 2.1 Heading-Aware Chunking (`rag/ingestion/chunker.py`)
- **Semantic Section Splitting:** Parses `#`, `##`, and `###` headers to preserve natural contextual boundaries rather than splitting arbitrarily across sentences.
- **Token Estimation & Sizing:** Calibrated for English financial prose (~1.3 tokens per word), targeting 300–500 tokens per chunk.
- **Overlap Protocol:** Applies 10%–15% token overlap across adjacent sections to retain connective context at boundary seams.
- **Content Hashing:** Computes SHA-256 digest of every chunk's text to enforce idempotent storage.

### 2.2 Provider-Agnostic Embeddings (`rag/embeddings/provider.py`)
- **Standard Protocol:** `EmbeddingProvider` defining `embed_text(text: str)`, `embed_batch(texts: list[str])`, and `dimension: int = 1536`.
- **Deterministic Local Provider (`DeterministicLocalEmbedding`):**
  - Combines word n-grams $(1, 2)$ and character n-grams $(3, 5)$ via sublinear hashing vectorization (8,192 features).
  - Multiplies by a Gaussian random projection matrix into 1,536 dimensions fixed by random seed 42.
  - Applies $L_2$ Euclidean unit normalization (`v / ||v||`), ensuring cosine similarity is directly computed via dot product.
  - Zero external network requests, zero heavy model downloads, 100% reproducible for offline CI/CD and tests.
- **OpenAI Provider (`OpenAIEmbeddingProvider`):** Available when `OPENAI_API_KEY` is provided, targeting `text-embedding-3-small`.

### 2.3 Idempotent Database Upsert (`rag/ingestion/pipeline.py`)
- Coordinates document traversal from `rag/documents/`.
- Queries existing database chunks by `doc_id` and `chunk_index`.
- If content SHA-256 matches existing record: flagged as `unchanged` (zero-cost no-op).
- If content has changed: updates chunk text, metadata, and recomputes embedding.
- Orphan cleanup: deletes obsolete chunk records if a document was revised with fewer total sections.
- **Verified Property:** Running ingestion repeatedly yields 0 duplicate rows and 0 redundant insertions.

---

## 3. Retriever Implementation (`rag/retrieval/retriever.py` & `backend/app/services/rag_service.py`)

- **Top-$k$ Ranking:** Returns top $k=4$ most relevant passages sorted by descending cosine similarity.
- **Dialect Adaptability:**
  - On PostgreSQL: Employs native `pgvector` operator `<=>` (cosine distance) with `ORDER BY embedding <=> :query LIMIT :top_k`.
  - On SQLite / In-Memory: Employs vectorized numpy dot product over unit-normalized embeddings.
- **Metadata Filters:** Supports precise filtering on `topic` and `language` JSONB metadata attributes.
- **Backend Service Layer:** `RAGService` exposed through FastAPI dependency `get_rag_service` for clean integration with the upcoming Phase 16 GenAI Agent Loop.

---

## 4. Evaluation Benchmark & Results

An extensive evaluation suite was executed across 54 realistic user questions paired with expected source documents (`rag/eval/eval_set.json`):

| Metric | Acceptance Target | Measured Result | Evaluation Status |
|---|---|---|---|
| **Total Evaluation Queries** | $\ge 40$ | **54** | **PASSED** |
| **hit@1** | Informational | **94.44%** (51/54) | **EXCELLENT** |
| **hit@4** | $\ge 85.0\%$ | **100.00%** (54/54) | **PASSED (Exceeded by +15.0%)** |
| **No-Result Rate** | $\le 5.0\%$ | **0.00%** (0/54) | **PASSED** |
| **Groundedness Pass Rate** | $\ge 85.0\%$ | **100.00%** (54/54) | **PASSED** |
| **Mean Top-1 Cosine Score** | $> 0.30$ | **0.3788** | **PASSED** |

The full query-by-query breakdown is exported at `docs/data/rag-eval-report.md`.

---

## 5. Security, Privacy & Content Compliance

1. **Zero User Data or PII Leakage (`backend/tests/security/test_rag_privacy.py`):**
   - Automated test scans every row in `rag_chunks`.
   - Confirms zero occurrences of email addresses, Bangladeshi phone numbers, user UUIDs, account passwords, JWT tokens, or transaction records.
   - Asserts that 100% of rows originate exclusively from authorized educational markdown files.
2. **Absence of "Guaranteed Returns" Language:**
   - Content compliance check scans all 54 documents in `rag/documents/` and all database chunk records for prohibited phrases (`guaranteed return`, `risk-free profit`, `guaranteed wealth`, `100% safe profit`, etc.).
   - Zero violations found. All investment documents state that returns are subject to market conditions and inflation.
3. **Database Idempotency:**
   - Ingestion tests verify that re-running ingestion does not alter row count or duplicate records.

---

## 6. Test Suite & Static Analysis Results

| Test Category | Suite File | Tests | Result |
|---|---|---|---|
| **RAG Unit & Pipeline** | `test_rag_pipeline.py` | 7 | **PASSED** |
| **RAG Privacy & Compliance** | `test_rag_privacy.py` | 2 | **PASSED** |
| **Integration & Dashboard Latency** | `test_dashboard_latency.py` | 1 | **PASSED** ($p95 = 33.44\text{ ms}$) |
| **Financial Engine Integration** | `test_goals_financial_engine.py` | 1 | **PASSED** |
| **ML & Simulation APIs** | `test_ml_and_simulation_apis.py` | 8 | **PASSED** |
| **Outbox & Transactions** | `test_transactions_outbox_dashboard.py` | 5 | **PASSED** |
| **Auth & Security** | `test_auth_security.py` | 16 | **PASSED** |
| **OpenAPI AuthZ Matrix** | `test_authz_matrix.py` | 2 | **PASSED** |
| **Log Hygiene** | `test_log_hygiene.py` | 2 | **PASSED** |
| **Schemathesis Fuzzing** | `test_openapi_schemathesis.py` | 27 | **PASSED** |
| **All Other Unit Tests** | Various (`test_financial_engine.py`, etc.) | 108 | **PASSED** |
| **Full Repository Test Suite** | `pytest backend/tests/` | **179** | **179 PASSED (100%)** |

### Static Quality Verification
- **Mypy Strict:** `mypy --config-file mypy.ini backend/app data/synthetic ml rag` $\to$ **Success: no issues found in 144 source files**.
- **Ruff Linter:** `ruff check backend ml data rag` $\to$ **All checks passed!**
- **Ruff Formatter:** `ruff format --check backend ml data rag` $\to$ **182 files formatted cleanly**.
