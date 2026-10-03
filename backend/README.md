# Backend Service (FastAPI)

FastAPI application providing the core API for **AI Financial Coach for MFS Users (Sohoj)**.

## Architecture
- `app/api/`: API router modules (v1 endpoints).
- `app/core/`: Application settings, security utilities, logging, middleware, and RFC 7807 error handlers.
- `app/financial/`: Pure deterministic financial calculation engine (`Decimal`, zero DB/ML/LLM dependencies).
- `app/models/`: SQLAlchemy 2.x ORM models.
- `app/schemas/`: Pydantic v2 validation models.
- `app/repositories/`: Database query and persistence abstractions.
- `app/services/`: Domain business logic and orchestration.
- `app/ai/`: LLM client integrations, prompt builders, tool definitions.
- `app/rag/`: Retrieval-Augmented Generation retrieval and vector storage bindings.
- `app/ml/`: Feature calculation and inference model integration.
- `app/workers/`: Background task processing (outbox, async anomaly detection).

## Running Tests & Checks
```bash
python -m pytest backend/tests
python -m ruff check backend
python -m mypy backend
```
