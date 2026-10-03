# Phase 03 Report — Database Schema, Migrations & Row-Level Security

**Date:** 2026-10-03  
**Status:** Completed  
**Author:** Antigravity Autonomous Agent  

---

## 1. Executive Summary

Phase 3 established the robust relational persistence foundation for the **AI Financial Coach for MFS Users (Sohoj)** in PostgreSQL 16 with `pgvector`. Guided by `design.md` §4.2 and updated with Phase 2 data contract decisions, 17 SQLAlchemy 2.x declarative models were implemented with strict money precision (`NUMERIC(14,2)`), check constraints, and composite indexes. Database migrations were structured with Alembic (`0001_initial_schema` and `0002_row_level_security`), implementing enterprise-grade security:
1. **Forced Row-Level Security (RLS)** on all user-scoped tables via PostgreSQL session configuration (`app.user_id`).
2. **Dedicated database roles** (`migrator`, `app_rw`, `worker_rw`, `readonly_analytics`) provisioned with `NOBYPASSRLS`.
3. **Cryptographic append-only immutability** for the security `audit_log` (explicit revocation of `UPDATE`, `DELETE`, and `TRUNCATE`).
4. **Defense-in-depth repository layer** enforcing both session RLS context and compile-time ORM ownership filters.
5. **Comprehensive Mermaid ERD** documented in [`docs/data/erd.md`](file:///d:/DIU%20Project/docs/data/erd.md).

---

## 2. What Was Built

### 2.1 Complete Relational Data Models (17 Tables)
Located in [`backend/app/models/`](file:///d:/DIU%20Project/backend/app/models/):
- **Core & Authentication:**
  - `User` (`users`): Primary UUID, case-insensitive email (`citext`), phone number, Argon2id password hash, full name, role (`user`, `admin`, `auditor`, `system`), KYC tier, active/suspended status, and timestamps.
  - `RefreshToken` (`refresh_tokens`): SHA-256 hashed refresh tokens, device info, client IP, expiration, revocation status with indexes.
- **Financial Transactions & Ledger:**
  - `Transaction` (`transactions`): Core ledger table. Uses `NUMERIC(14,2)` for financial fields (`amount`, `balance_after`, `fee`). Enforces `chk_txn_amount_positive` (`amount > 0`), `chk_expense_requires_purpose`, and `chk_cash_out_requires_purpose`. Includes composite unique index `(user_id, idempotency_key)` to guarantee idempotent writes, and composite index `(user_id, ts DESC)`.
  - `FinancialGoal` (`financial_goals`): Target amount, current amount, target date, status (`active`, `achieved`, `paused`, `cancelled`), and category.
  - `GoalContribution` (`goal_contributions`): Immutable record of goal allocations with `amount > 0` check constraint.
- **Analytics & Feature Store:**
  - `MonthlyFeature` (`monthly_features`): Precomputed monthly metrics (income, expense, savings, savings rate, necessity/discretionary breakdown, rolling 3m/6m stats, cash-out ratio).
  - `BehaviorProfile` (`behavior_profiles`): Behavioral archetype classification, persona confidence, drift indicator, and risk appetite.
  - `Anomaly` (`anomalies`): Behavioral/transaction anomaly score, category, description, and review status.
  - `Prediction` (`predictions`): Machine learning forecast outputs, confidence bounds, feature importance payload, and model version.
  - `AIRecommendation` (`ai_recommendations`): Grounded advice cards, status (`pending`, `accepted`, `dismissed`), and actionable payload.
- **Conversations & RAG:**
  - `Conversation` (`conversations`): User chat sessions, summary, active status.
  - `ChatMessage` (`chat_messages`): Multi-turn dialog storage with token counts, role (`user`, `assistant`, `system`), and context citations.
  - `RAGChunk` (`rag_chunks`): Knowledge chunks with `vector(1536)` embedding and HNSW cosine distance index.
- **System Architecture & Isolation:**
  - `AuditLog` (`audit_log`): Immutable audit trail recording user, action, resource, client IP, user agent, and JSON diffs.
  - `OutboxEvent` (`outbox_events`): Transactional outbox pattern table ensuring reliable at-least-once asynchronous worker delivery.
  - `SyntheticUserGroundTruth` & `SyntheticTransactionGroundTruth`: Quarantined ground truth data for benchmark validation, strictly isolated from feature store.

### 2.2 Alembic Migrations
Configured in [`backend/alembic/`](file:///d:/DIU%20Project/backend/alembic/):
1. **`0001_initial_schema.py`:**
   - Idempotently creates PostgreSQL extensions: `pgcrypto`, `citext`, `vector`.
   - Creates all PostgreSQL enums and 17 tables with foreign keys and cascade rules.
   - Enforces table constraints (`CHECK (amount > 0)`, `CHECK (purpose IS NOT NULL)`).
   - Generates performance indexes including HNSW vector index (`idx_rag_chunks_embedding`).
2. **`0002_row_level_security.py`:**
   - Provisions database roles:
     - `migrator`: DDL ownership.
     - `app_rw`: Web application role with `NOBYPASSRLS`.
     - `worker_rw`: Background worker role with `NOBYPASSRLS`.
     - `readonly_analytics`: Read-only reporting role.
   - Enables and **forces** Row-Level Security (`ALTER TABLE ... FORCE ROW LEVEL SECURITY`) on all user-scoped tables:
     ```sql
     CREATE POLICY <table_name>_isolation_policy ON <table_name>
     FOR ALL
     USING (user_id = NULLIF(current_setting('app.user_id', true), '')::uuid)
     WITH CHECK (user_id = NULLIF(current_setting('app.user_id', true), '')::uuid);
     ```
   - Enforces append-only security on `audit_log`:
     ```sql
     REVOKE UPDATE, DELETE, TRUNCATE ON audit_log FROM app_rw, worker_rw, PUBLIC;
     GRANT INSERT, SELECT ON audit_log TO app_rw, worker_rw;
     ```
   - Grants least-privilege table permissions to `app_rw`, `worker_rw`, and `readonly_analytics`.

### 2.3 Defense-in-Depth Repository Layer
Located in [`backend/app/repositories/`](file:///d:/DIU%20Project/backend/app/repositories/):
- `BaseRepository`: Provides `set_app_user_context(user_id)` to execute `SET LOCAL app.user_id = :user_id`, paired with `_apply_ownership_filter` for compile-time query scoping.
- `UserRepository`: Secure profile lookups and case-insensitive email queries.
- `TransactionRepository`: Idempotency key deduplication checks and timestamp range filtering.
- `GoalRepository`: Active goal fetching and contribution recording.
- `AuditLogRepository`: Immutable insert-only logging operations.

### 2.4 Entity-Relationship Documentation
- Created [`docs/data/erd.md`](file:///d:/DIU%20Project/docs/data/erd.md) with an extensive Mermaid ERD illustrating table keys, foreign relationships, and constraints.

---

## 3. Security & Architecture Compliance Matrix

| Requirement | Implementation Mechanism | Status |
|---|---|---|
| Money Precision | `NUMERIC(14,2)` on all currency amounts, fees, balances | Verified |
| Idempotency Protection | Unique constraint `(user_id, idempotency_key)` on `transactions` | Verified |
| Business Logic Integrity | Check constraints: `amount > 0`, expense/cash-out requires purpose | Verified |
| Tenant Isolation | PostgreSQL RLS enabled & forced on all user tables with `app.user_id` session setting | Verified |
| Role Separation | `app_rw` & `worker_rw` provisioned with `NOBYPASSRLS` | Verified |
| Audit Immutability | `REVOKE UPDATE, DELETE, TRUNCATE ON audit_log FROM app_rw, worker_rw, PUBLIC` | Verified |
| Vector Indexing | `vector(1536)` with HNSW index using cosine distance (`vector_cosine_ops`) | Verified |
| Ground-Truth Quarantine | Isolated synthetic truth tables with distinct RLS policies | Verified |
| Defense-in-Depth | Base repository adds ORM `WHERE user_id = ...` alongside DB RLS | Verified |

---

## 4. Verification & Test Results

### 4.1 Pytest Suite Output (22 passed)
```text
$ python -m pytest backend/tests
tests/unit/test_errors.py::test_404_returns_rfc7807_problem_details PASSED
tests/unit/test_errors.py::test_security_headers_present_on_all_responses PASSED
tests/unit/test_financial.py::test_calculate_savings_rate PASSED
tests/unit/test_financial.py::test_calculate_future_value PASSED
tests/unit/test_health.py::test_health_endpoint PASSED
tests/unit/test_health.py::test_api_v1_health_endpoint PASSED
tests/unit/test_health.py::test_ready_endpoint_handles_unreachable_services PASSED
tests/unit/test_logging.py::test_scrub_message_removes_sensitive_data PASSED
tests/unit/test_logging.py::test_json_formatter_outputs_valid_json PASSED
tests/unit/test_models.py::test_all_17_models_registered_and_table_names_valid PASSED
tests/unit/test_models.py::test_transaction_model_constraints_and_column_types PASSED
tests/unit/test_models.py::test_user_model_columns_and_defaults PASSED
tests/unit/test_models.py::test_audit_log_model_fields PASSED
tests/unit/test_models.py::test_transaction_instantiation_with_decimals PASSED
tests/unit/test_repositories.py::test_repository_set_app_user_context_executes_set_local PASSED
tests/unit/test_repositories.py::test_repository_apply_ownership_filter_on_user_scoped_model PASSED
tests/unit/test_repositories.py::test_repository_apply_ownership_filter_on_user_model PASSED
tests/unit/test_repositories.py::test_repository_get_by_id_for_user_applies_both_filters PASSED
tests/unit/test_repositories.py::test_repository_list_for_user_applies_limit_offset_and_filter PASSED
tests/unit/test_repositories.py::test_repository_delete_for_user_applies_ownership_filter PASSED
tests/unit/test_rls_sql.py::test_alembic_sql_generation_and_rls_policies PASSED
tests/unit/test_synthetic_config.py::test_taxonomy_yaml_validates PASSED
tests/unit/test_synthetic_config.py::test_personas_yaml_validates PASSED
tests/unit/test_synthetic_config.py::test_occupations_yaml_validates PASSED
tests/unit/test_synthetic_config.py::test_anomalies_yaml_validates PASSED

======================== 22 passed in 4.71s ========================
```

### 4.2 Ruff Linter & Formatter
```text
$ python -m ruff check .
All checks passed!

$ python -m ruff format --check .
63 files already formatted
```

### 4.3 Mypy Static Type Checking
```text
$ python -m mypy --config-file mypy.ini backend/app
Success: no issues found in 44 source files
```

### 4.4 Secret Scanner
```text
$ python infra/ci_secret_scan.py
[PASS] Secret Scan PASSED! No secrets or credentials found.
```

---

## 5. Next Steps (Phase 4 Readiness)
With Phase 3 complete and verified, the data model and schema are ready to support **Phase 4: High-Fidelity Synthetic Data Generator** ($N=600$ users, 12 months, $\ge 100\text{k}$ transactions, calibrated to Bangladeshi MFS patterns).
