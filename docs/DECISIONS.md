# Architectural Decision Records (ADRs)

This document tracks key architectural decisions, rationale, context, and consequences across the project lifecycle.

---

## ADR-0001: ADR Format & Decision Record Standard

- **Status:** Accepted
- **Date:** 2026-10-03
- **Context:** `design.md` and `security.md` define architectural and security contracts. As development progresses, decisions regarding ambiguities or structural trade-offs must be transparently documented and preserved.
- **Decision:** Use a lightweight, numbered ADR format with Status, Date, Context, Decision, and Consequences sections.
- **Consequences:** All non-trivial decisions will be recorded here and linked in `docs/PROGRESS.md`.

---

## ADR-0002: Docker Compose Port Exposure & Dev Override Isolation

- **Status:** Accepted
- **Date:** 2026-10-03
- **Context:** `security.md` §14.1 and §14.2 mandate that PostgreSQL, Redis, and internal services must NOT publish ports to the host by default. However, local developer productivity may require direct database/cache inspection via GUI tools (e.g. DBeaver, TablePlus).
- **Decision:** Keep `docker-compose.yml` strictly non-publishing on an internal bridge network. Provide `docker-compose.override.yml.example` for developers to copy locally to `docker-compose.override.yml`, which is ignored in `.gitignore`.
- **Consequences:** Zero risk of unintended host port exposure in CI, staging, or production environments while maintaining developer flexibility.

---

## ADR-0003: Pure Deterministic Financial Engine Isolation

- **Status:** Accepted
- **Date:** 2026-10-03
- **Context:** Financial calculations (interest, savings rates, loan amortizations, projections) must be 100% deterministic, audit-compliant, and free of floating-point inaccuracies.
- **Decision:** The `backend/app/financial` module must be implemented as a pure Python library utilizing `decimal.Decimal` exclusively. It is strictly forbidden from importing database sessions, models, ML libraries, or LLM clients. Mypy strict mode will be enforced on this package.
- **Consequences:** Calculations are completely reproducible, fast to test, and can be certified independently of infrastructure or AI models.

---

## ADR-0004: RFC 7807 Problem Details Error Representation

- **Status:** Accepted
- **Date:** 2026-10-03
- **Context:** `design.md` §9.3 and `security.md` §13 require standard, machine-readable, and secure error responses that do not leak internal stack traces or database schema details.
- **Decision:** Adopt RFC 7807 (`application/problem+json`) with standard fields: `type`, `title`, `status`, `detail`, `instance`, `code`, and optional `errors` for validation failure arrays.
- **Consequences:** Consistent API error contracts across all endpoints for frontend clients and automated API consumers.

---

## ADR-0005: Dual-Layer Tenant Isolation via Forced RLS and Repository Scoping

- **Status:** Accepted
- **Date:** 2026-10-03
- **Context:** Mobile Financial Services (MFS) users store sensitive personal financial transaction and goal data. A failure in application-layer filtering or an accidental missing `WHERE user_id = ...` clause could leak another tenant's financial history.
- **Decision:** Implement defense-in-depth isolation:
  1. PostgreSQL Row-Level Security (RLS) is enabled and **forced** on all user-scoped tables with session policy `USING (user_id = NULLIF(current_setting('app.user_id', true), '')::uuid)`.
  2. Database roles `app_rw` and `worker_rw` are provisioned with `NOBYPASSRLS`.
  3. The repository layer enforces `set_app_user_context(user_id)` to execute `SET LOCAL app.user_id = :user_id` on the transaction session, and automatically prepends `WHERE user_id = :user_id` at the ORM query level.
- **Consequences:** Even if an ORM query omission occurs or a raw SQL injection is attempted, PostgreSQL engine-level RLS physically blocks cross-tenant row access.

---

## ADR-0006: Cryptographic & Relational Append-Only Audit Logging

- **Status:** Accepted
- **Date:** 2026-10-03
- **Context:** Security audits and financial regulatory standards mandate that audit logs cannot be tampered with, modified, or truncated by application services or compromised application credentials.
- **Decision:**
  1. `audit_log` table permissions revoke `UPDATE`, `DELETE`, and `TRUNCATE` from `app_rw`, `worker_rw`, and `PUBLIC`.
  2. Only `INSERT` and `SELECT` permissions are granted.
  3. Schema updates and retention pruning may only be executed by the `migrator` role during designated maintenance windows.
- **Consequences:** Audit history is tamper-resistant against application vulnerabilities or credential compromise.
