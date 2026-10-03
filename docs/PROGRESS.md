# Project Progress & Roadmap

## Phase Status Summary

| Phase | Description | Status | Completion Date |
|---|---|---|---|
| **Phase 1** | Repository Bootstrap, Tooling & Environment | **Completed** | 2026-10-03 |
| **Phase 2** | Domain Definitions, Data Contract & Persona Specification | **Completed** | 2026-10-03 |
| **Phase 3** | Database Schema, Migrations & Row-Level Security | **Completed** | 2026-10-03 |
| **Phase 4** | High-Fidelity Synthetic Data Generator | **Completed** | 2026-10-03 |
| **Phase 5** | Data Generation Run, Load & Realism Validation | **Completed** | 2026-10-03 |
| **Phase 6** | EDA & Data Quality Analysis | **Completed** | 2026-10-03 |
| **Phase 7** | Feature Engineering & ML Pipeline | **Completed** | 2026-10-03 |
| **Phase 8** | ML Model A: Behavior Classification | **Completed** | 2026-10-03 |
| **Phase 9** | ML Model B: Anomaly Detection | **Completed** | 2026-10-03 |
| **Phase 10** | ML Model C: Expense Forecasting + Model Registry & Serving | **Completed** | 2026-10-03 |
| **Phase 11** | Financial Engine (Deterministic) | **Completed** | 2026-10-03 |
| **Phase 12** | Backend Core: Auth, Users & Security Foundation | **Completed** | 2026-10-03 |
| **Phase 13** | Backend API: Transactions, Goals, Financial Context & Async Worker | **Completed** | 2026-10-03 |
| **Phase 14** | ML, Forecast & Simulation APIs; Anomaly Pipeline Integration | **Completed** | 2026-10-03 |
| **Phase 15** | RAG Knowledge Base | **Completed** | 2026-10-03 |
| **Phase 16** | GenAI Agent: Tools, Context Builder, Prompts & Safety Layer | **Completed** | 2026-10-03 |
| **Phase 17** | Chat API, Conversations & AI Evaluation Suite | **Completed** | 2026-10-03 |
| **Phase 18** | Frontend Foundation, Dashboard, Transactions, Goals & Simulator | **Completed** | 2026-10-03 |
| **Phase 19** | Behavior & Anomaly UI, AI Coach UI, End-to-End Tests | **Completed** | 2026-10-04 |
| **Phase 20** | Monitoring, Security Hardening, Deployment & Final Acceptance | **Completed** | 2026-10-04 |

---

## Phase 20 Checklist (Completed)
- [x] Prometheus metrics & observability:
  - Request counters, duration histograms, DB pool gauges, outbox event queue/lag gauges, ML inference and drift metrics (`ml_drift_psi_score`, `ml_drift_ks_statistic`, `ml_forecast_mape`)
  - Continuous drift evaluation worker (`app.worker.drift_job`)
  - Grafana dashboards as code (`sohoj-overview.json`, `sohoj-security-ml.json`)
  - Prometheus alert rules (`alert_rules.yml`) matching `security.md` §13.3
- [x] Security hardening & audits:
  - Bandit SAST: 0 Medium, 0 High issues across 10,954 LOC in `backend/app`
  - Zero vulnerable dependencies (`pip-audit` clean, `npm audit` clean)
  - Pre-launch security checklist completed with full evidence in `docs/security/checklist-results.md`
  - RFC 9116 compliant `/.well-known/security.txt` and root `SECURITY.md`
- [x] Emergency kill switches & admin token revocation:
  - Enforced `AI_ENABLED`, `REGISTRATION_ENABLED`, `LOGIN_ENABLED`, `FORECAST_ENABLED` (HTTP 503)
  - Admin token revocation endpoint `POST /api/v1/admin/revoke-tokens` with constant-time key verification
- [x] Hardened container deployment & disaster recovery:
  - Hardened `docker-compose.prod.yml` (zero public internal exposure, Caddy reverse proxy only, non-root `UID 10001`, `read_only: true`, `cap_drop: [ALL]`, `no-new-privileges: true`)
  - Database backup and restore scripts (`scripts/backup_db.py`, `scripts/restore_db.py`)
  - Automated disaster recovery restore drill executed with SHA-256 verification and 100% data match (`docs/security/restore-drill.log`)
  - Enhanced GitHub Actions CI workflow with staging smoke tests
- [x] 50-User concurrent load testing:
  - Locust test simulating 50 virtual users executing 5,989 requests at 313 req/s
  - 0.00% error rate, dashboard p95 at 91ms (< 500ms target), chat p95 at 86ms (< 10s target)
  - Full benchmark report in `docs/performance/load-test-report.md`
- [x] Complete documentation suite & model cards:
  - Comprehensive `README.md`, `docs/RUNBOOK.md`, `docs/ARCHITECTURE.md`, `docs/demo-script.md`
  - 3 detailed Model Cards in `docs/ML-CARDS/` (Model A Persona, Model B Anomaly, Model C Forecaster)
  - Reproducible setup script `setup.ps1` and enhanced `Makefile`
  - Final project acceptance report `docs/FINAL-REPORT.md`

---

## Phase 19 Checklist (Completed)
- [x] Behavior & Anomaly surface (`/behavior`):
  - Calibrated financial archetype card with confidence score, model version, and cold-start fallback callout
  - 5 factor explainability bars (Savings Rate, Necessity Ratio, Discretionary Ratio, Cash-Out Count, Volatility) benchmarked against 50/30/20 guideline
  - Spending & savings allocation trend chart with trailing 6-month historical stacked bar visualization
  - Outlier anomaly list with status filter pills (`all`, `open`, `confirmed`, `dismissed`) and interactive confirm/dismiss mutations
  - Grounded behavioral coaching insights cards with priority badges and source citations
- [x] Conversational AI Coach (`/coach`):
  - Server-Sent Events (SSE) streaming chat consuming `token`, `tool_status`, `ui_action`, and `done` events
  - Interactive Tool-Status chips rendering execution states across 15 backend financial tools
  - Deep-link UI action buttons with target validation against server allow-list
  - Safe Markdown AST token renderer with zero `dangerouslySetInnerHTML` and safe link protocol sanitization
  - Educational AI consent onboarding gate (`ConsentGate`) requiring user opt-in before LLM invocation
  - Trust badges: permanent "Grounded AI" badge, prompt version tag, and thumbs up/down user feedback rating
- [x] Full End-to-End User Journey (Playwright `full-flow.spec.ts`):
  - 7-step test passing in headless CI: Register with AI consent → Record Cash-Out with mandatory purpose → Verify on `/transactions` → Inspect `/behavior` → Create Goal on `/goals` → Simulate compound growth & doubling on `/simulator` → Ask Coach "Can I afford ৳5,000?" and verify grounded numbers
- [x] Accessibility Audit (Playwright + Axe-Core `accessibility.spec.ts`):
  - 4/4 pages passed with zero critical accessibility violations (`/login`, `/register`, `/dashboard`, `/simulator`)
- [x] Security & Tenant Isolation (Playwright `security.spec.ts`):
  - Unauthenticated route protection redirects to `/login`
  - Logout clears authentication tokens and revokes access
  - XSS injection payloads in merchant and description fields render completely inert
- [x] 100% test pass rate:
  - Vitest: 22/22 unit and component tests passing
  - Playwright: 8/8 end-to-end tests passing
  - TypeScript: `tsc --noEmit` clean (0 errors)
  - ESLint: clean (0 errors/warnings)
- [x] High-resolution desktop and mobile UI screenshots archived in `docs/ui/screens/`
- [x] Comprehensive phase report authored at `docs/phase-reports/phase-19.md`

---

## Phase 18 Checklist (Completed)
- [x] Next.js 14 App Router + TypeScript + Tailwind CSS setup with TanStack Query v5
- [x] In-memory access token storage with automatic silent token refresh via HttpOnly cookie (zero tokens in Web Storage)
- [x] Edge middleware for strict Content Security Policy (CSP nonces) and route protection
- [x] Next.js reverse proxy rewrites mapping `/api/v1/:path*` to `http://127.0.0.1:8000/api/v1/:path*` for unified same-origin cookies
- [x] 8 complete application pages: `/login`, `/register`, `/dashboard`, `/transactions`, `/goals`, `/simulator`, `/profile`, and `/settings`
- [x] All 11 core dashboard components implemented (`design.md` §10):
  - `BalanceCard`, `IncomeCard`, `ExpenseCard`, `SavingsCard`
  - `SavingsRateChart`, `ExpenseCategoryChart`, `MonthlyExpenseChart`
  - `FinancialGoalCard`, `ForecastCard`, `AnomalyCard`, `AIInsightCard`
- [x] `CashOutPurposeModal` with mandatory purpose selection (`necessity`, `savings_goal`, `discretionary`, `other`), subcategories, MFS selector, and idempotency key
- [x] Wealth Simulator (`SimulatorView`) calling `/api/v1/simulate/growth` and `/simulate/doubling` (zero duplicated math in JS) with permanently visible **Assumed-rate badge** and disclaimer
- [x] Empty, low-data, loading, and error states across all dashboard widgets and views
- [x] Bangladesh localization: `Intl.NumberFormat('en-BD')` for ৳, Asia/Dhaka timezone formatting, and externalized string dictionary (`lib/i18n.ts`)
- [x] Comprehensive Vitest and React Testing Library suite (11/11 tests passing)
- [x] Zero TypeScript compilation errors (`tsc --noEmit`) and zero ESLint issues (`npm run lint`)
- [x] Lighthouse audit on `/dashboard`: **Accessibility Score 93** (target $\ge 90$), Best Practices 96, SEO 100
- [x] Visual verification across desktop and mobile (390px) viewports with 8 screenshots saved to `docs/ui/screens/`
- [x] Phase report authored at `docs/phase-reports/phase-18.md`

---

## Phase 17 Checklist (Completed)
- [x] High-performance `POST /api/v1/chat` supporting Server-Sent Events (SSE) streaming (`tool_status`, `token`, `ui_action`, `done`) and standard JSON responses
- [x] Thread history retrieval (`GET /api/v1/chat/history`) and message feedback rating submission (`POST /api/v1/chat/{message_id}/feedback`)
- [x] `ConversationManager` implementing 6-turn (12-message) sliding context window, progressive summarization for older history, and automated title derivation
- [x] `ChatRepository` managing conversations, messages with execution traces, token telemetry, latency, and automated 90-day retention purging job
- [x] Operational resilience & circuit breaker (`LLMCircuitBreaker`): three states (`CLOSED`, `OPEN`, `HALF_OPEN`), 30s recovery timeout, and graceful fallback guidance
- [x] Daily token budget manager (`TokenBudgetManager`): 50,000 tokens/user/day limit with RFC 7807 429 Too Many Requests response
- [x] Zero 5xx guarantee: all upstream LLM provider failures degrade gracefully into safe, grounded advice without dropping connections or returning 500 errors
- [x] Golden conversation suite (`backend/tests/evaluation/test_golden_suite.py`) with 62 test cases spanning 10 critical financial domains
- [x] Evaluation benchmarks verified:
  - **Numeric Faithfulness:** **100.0%** (target $\ge 99\%$)
  - **Tool Selection Accuracy:** **100.0%** (target $\ge 95\%$)
  - **Refusal Correctness:** **100.0%** (target $100\%$)
  - **Projection Disclaimer Rate:** **100.0%** (target $\ge 95\%$)
  - **Turn Latency:** **3.98 ms** average / **5.56 ms** p95 (target $< 250\text{ ms}$)
- [x] Realistic demo transcripts generated across 5 synthetic personas: `docs/ai/demo-transcripts.md`
- [x] Comprehensive evaluation report published: `docs/ai/eval-report.md`
- [x] Full integration test suite passing: `backend/tests/integration/test_chat_api.py` (6 integration tests)
- [x] Total platform test suite: **210/210 tests passing** in `backend/tests/`
- [x] Strict static verification: 100% `mypy` clean, 100% `ruff` clean
- [x] Comprehensive phase report created at `docs/phase-reports/phase-17.md`

---

## Phase 16 Checklist (Completed)
- [x] Provider-agnostic `LLMClient` protocol and async `OpenAILLMClient` adapter with function-calling support
- [x] Deterministic `MockLLM` replaying scripted tool-turn sequences, exceptions, and inspection of recorded calls
- [x] `ToolManager` with Pydantic v2 argument validation (`extra="forbid"`), per-turn budget enforcement ($\le 6$ calls), execution timeout (5.0s), and server-side `user_id` injection from authenticated JWT
- [x] All 15 concrete financial tools implemented (`FinancialToolSet`): `get_user_profile`, `get_current_balance`, `get_transactions` (capped $\le 50$), `get_monthly_summary`, `get_behavior_profile`, `get_spending_forecast`, `get_anomalies`, `get_financial_goals`, `calculate_future_value`, `calculate_doubling_time`, `calculate_goal_plan`, `calculate_savings_rate`, `run_financial_scenario`, `check_affordability`, and `search_knowledge`
- [x] `ContextBuilder` generating compact aggregates with zero PII (no names, emails, phone numbers, or raw transaction dumps) and emitting per-request `data_manifest` for audit
- [x] Modular prompt management system (`PromptManager`, version `"2026.10.1"`) compiling `system.md`, `tools_policy.md`, `response_style.md`, and few-shot examples
- [x] Missing parameter protocol: agent asks the user directly instead of guessing rates or horizons (Safety Principle 10)
- [x] Multi-stage safety layer:
  - `ConsentGate`: blocks queries immediately with `ConsentRequiredError` if `consent_ai=False` (zero LLM calls)
  - `InputGuard`: prompt-injection heuristics, scope verification (finance-only), length ceiling, and PII masking
  - `AdviceBoundaryValidator`: refuses specific stock advice, disallows absolute guarantees, blocks autonomous money movements, and enforces projection disclaimers
  - `NumericGroundingValidator`: verifies every number/percentage against context and tool results; retries once on mismatch, then activates deterministic fallback
  - `OutputSanitizer`: strips HTML tags, sanitizes links, and enforces allowed UI actions (`navigate_to_goals`, `open_simulator`, etc.)
- [x] Orchestrator (`FinancialAgent.run_turn`) tying all stages into an end-to-end conversational turn
- [x] Comprehensive adversarial security test suite (`backend/tests/security/prompt_injection/test_prompt_injection.py`) testing merchant description injection, system prompt extraction, jailbreaks, and RAG poisoning
- [x] 24/24 Phase 16 unit and security tests passing; **203/203 full backend tests passing**
- [x] 100% `mypy` clean (0 issues in 18 source files in `backend/app/ai`) and 100% `ruff` clean
- [x] Comprehensive report created at `docs/phase-reports/phase-16.md`

## Phase 15 Checklist (Completed)
- [x] Curated corpus authored in `rag/documents/`: 54 agent-authored, original educational documents across 11 financial topics with YAML front-matter (`title`, `topic`, `language`, `version`)
- [x] Document parser (`rag/ingestion/parser.py`) extracting front-matter metadata and clean markdown text
- [x] Heading-aware chunker (`rag/ingestion/chunker.py`) with 300–500 token target sizing, 10–15% overlap, and heading hierarchy preservation
- [x] Provider-agnostic embedding abstraction (`rag/embeddings/provider.py`) with `DeterministicLocalEmbedding` (1536 dims, normalized unit vectors) and pluggable OpenAI support
- [x] Ingestion pipeline (`rag/ingestion/pipeline.py`) with idempotent upsert based on content SHA-256 hashes and automatic orphan chunk cleanup
- [x] Vector retriever (`rag/retrieval/retriever.py`) supporting top-4 cosine similarity search, pgvector `<=>` distance, and SQLite/numpy dot product fallback
- [x] Metadata filtering by `topic` and `language` implemented and tested
- [x] Backend service layer (`backend/app/services/rag_service.py` & `deps.py`) exposing `search_knowledge` for downstream GenAI agent loop integration
- [x] Curated 54-item evaluation benchmark (`rag/eval/eval_set.json`) covering all topics and concepts
- [x] Evaluation runner (`rag/eval/evaluate.py`) achieving **100% hit@4** (well above $\ge 85\%$ acceptance criterion) and **94.44% hit@1** with 0% no-result rate
- [x] Evaluation report published to `docs/data/rag-eval-report.md`
- [x] Security guarantee verified: automated test (`test_rag_privacy.py`) verifies zero user transactions or PII ever enter `rag_chunks`
- [x] Content compliance verified: automated scanner confirms total absence of "guaranteed returns" or risk-free investment language
- [x] Full test suite passing (179/179 tests), strict `mypy` passing across 144 files, and `ruff` format/lint clean
- [x] Comprehensive report created at `docs/phase-reports/phase-15.md`

## Phase 14 Checklist (Completed)
- [x] RFC 7807 `InsufficientDataError` handling (`INSUFFICIENT_DATA` code + actionable guidance) for cold-start users (< 2 months history)
- [x] `MLService` encapsulating Model A (Behavior Classification), Model B (Anomaly Detection), and Model C (Expense & Savings Forecasting)
- [x] Debounced behavior profile recomputation (<= 1 per 15 minutes per user) caching active profile outputs
- [x] Transaction-level anomaly detection pipeline with peer-group fallback when category sample size < 5
- [x] End-to-end Transactional Outbox integration: `transaction.created` events trigger anomaly scoring and store linked `AIRecommendation` items with `source_refs`
- [x] Behavioral insight generation without LLM nondeterminism (deterministic rules linked to detected anomaly and feature telemetry)
- [x] Forecast endpoints (`GET /forecast/expenses`, `GET /forecast/savings`) with quantile prediction intervals (p10, p50, p90) and 3-month MA baseline fallback
- [x] Financial Simulation endpoints (`POST /simulate/growth`, `/simulate/goal`, `/simulate/doubling`, `/simulate/scenario`) wrapping pure Financial Engine
- [x] Strict `Decimal` arithmetic (`ROUND_HALF_UP`), mandatory `assumptions` block, and `disclaimer_code="PROJECTION_NOT_GUARANTEED"` on all projections
- [x] Anomaly feedback endpoint (`PATCH /anomalies/{anomaly_id}`) supporting `dismissed` and `confirmed` status updates with strict tenant isolation (404 on cross-tenant access)
- [x] Automated dashboard endpoint latency benchmark verifying p95 < 500 ms SLA (**measured: p95 = 33.44 ms**)
- [x] OpenAPI-driven authorization matrix test updated to cover anomaly endpoints (8 parameterized routes verified)
- [x] Schemathesis fuzzing and full test suite passing (170/170 tests passing)
- [x] Strict typing verified: `mypy` clean across 131 source files; `ruff` formatting and linting clean
- [x] Comprehensive report created at `docs/phase-reports/phase-14.md`

## Phase 13 Checklist (Completed)
- [x] Transaction APIs (`POST/GET /api/v1/transactions`, `GET/DELETE /api/v1/transactions/{id}`) with strict Decimal arithmetic, positive bounds, and enum whitelists
- [x] Cash-out APIs (`POST/GET /api/v1/cashouts`) with strictly enforced mandatory `purpose`
- [x] Idempotency keys (`idempotency_key` payload attribute or `Idempotency-Key` header) guaranteeing safe retries
- [x] Deterministic cursor-based pagination with ISO-8601 timestamps and tie-breaker UUIDs
- [x] Transactional Outbox pattern: atomicity between transaction/cash-out inserts and `outbox_events` logging
- [x] Background outbox worker (`app/worker/outbox_worker.py` + Arq) draining events, recomputing `monthly_features` via `MonthlyFeatureEngine`, and invalidating dashboard cache
- [x] Worker offline resilience: API writes succeed during worker outages; worker drains accumulated queue on restart
- [x] Financial Goals APIs (`POST/GET /api/v1/goals`, `GET/PATCH/DELETE /api/v1/goals/{id}`, `POST/GET /api/v1/goals/{id}/contributions`)
- [x] Pure deterministic Financial Engine integration (`calculate_goal_progress`): completion %, shortfall, remaining months, required monthly saving, ETA, and feasibility status
- [x] Dashboard APIs (`/api/v1/dashboard`, `/api/v1/dashboard/monthly`, `/api/v1/dashboard/categories`) with KPI summaries, monthly feature time series, and category breakdowns
- [x] Multi-tier caching (`CacheManager` Redis primary + memory fallback, $\le 60\text{ s}$ TTL) with immediate write-driven invalidation
- [x] OpenAPI-driven cross-tenant AuthZ security matrix test verifying 404 Not Found across all parameterized endpoints
- [x] Multi-tenant isolation verified under concurrent load with PostgreSQL RLS
- [x] Schemathesis property-based fuzz tests across all 25+ routes with zero 5xx server errors
- [x] Complete test suite passing (161/161 tests), 100% `mypy` strict passing (117 files), and 100% `ruff` clean
- [x] Comprehensive Phase 13 completion report written to `docs/phase-reports/phase-13.md`

---

## Phase 12 Checklist (Completed)
- [x] Argon2id password hashing ($m=64\text{ MiB}, t=3, p=4$) with length $\ge 12$ and offline breached-password catalog validation
- [x] JWT access tokens (15-minute expiry, pinned `HS256` algorithm, strict `iss="sohoj-auth"`, `aud="sohoj-client"`, `jti`, `exp`, `sub`)
- [x] Opaque refresh token generation, SHA-256 hashed storage in database, and hardened `HttpOnly; Secure; SameSite=Lax` cookie
- [x] Refresh token rotation with immediate reuse detection revoking the compromised user token family
- [x] Brute-force protection: sliding-window rate limiting (Redis + in-memory fallback) and dual-threshold account lockout (5 failures $\to$ 15-minute 429 lockout)
- [x] Request-scoped PostgreSQL Row-Level Security context injection (`SET LOCAL app.user_id = :user_id`) executed on database session
- [x] Security headers middleware (`HSTS`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Content-Security-Policy`, `Referrer-Policy`)
- [x] Request body size limit middleware (enforces 10 MB maximum payload size)
- [x] User management endpoints (`/api/v1/users/me` GET, PATCH with strict `extra="forbid"` mass-assignment prevention)
- [x] User data rights & GDPR compliance: `GET /api/v1/users/me/export` and `DELETE /api/v1/users/me` account erasure
- [x] AI consent management (`consent_ai` boolean flag with audit logging of modifications)
- [x] Append-only audit logging for authentication successes, failures, lockouts, token reuse, consent alterations, and account operations
- [x] Production profile protection: `/docs`, `/redoc`, and `/openapi.json` disabled in production environment
- [x] Comprehensive log hygiene with `JSONFormatter` scrubbing passwords, Bearer tokens, refresh tokens, emails, and phone numbers
- [x] OpenAPI contract validation and Schemathesis property-based fuzz testing verifying zero 5xx server errors
- [x] 29/29 dedicated security tests passing (`backend/tests/security/`), 137/137 total repository tests passing
- [x] Full `mypy` strict compliance (103 source files clean) and `ruff` linting/formatting clean
- [x] Comprehensive Phase 12 completion report written to `docs/phase-reports/phase-12.md`

---

## Phase 11 Checklist (Completed)
- [x] Pure deterministic financial engine implemented in `backend/app/financial/engine.py` adhering to `design.md` §6
- [x] Absolute boundary isolation: 0 dependencies on DB, ORM, ML, AI, FastAPI, or SQLAlchemy (enforced by AST import test)
- [x] Strict Decimal arithmetic and centralized rounding policy in `backend/app/financial/rounding.py` (`ROUND_HALF_UP`, currency to 2 decimals, rates to 4, ratios to 6)
- [x] Typed return dataclasses in `backend/app/financial/schemas.py` with mandatory `AssumptionsBlock` (`rate_type: "assumed" | "historical" | "contractual"`)
- [x] Strongly typed exception hierarchy in `backend/app/financial/exceptions.py` (`NegativeValueError`, `ZeroPeriodError`, `InvalidRateError`, `InvalidCompoundingFrequencyError`, `InvalidTimingError`, `InvalidTargetDateError`)
- [x] Future Value engine (`calculate_future_value`) supporting lump sum, monthly annuity, ordinary/due timing, compounding frequencies (1, 2, 4, 12, 365), and $r=0$ special case
- [x] Doubling time engine (`calculate_doubling_time`) with exact continuous/compound closed form and Rule of 72 approximation
- [x] Required saving engine (`calculate_monthly_required_saving`) solving annuity accumulation equation with zero-rate and growth-sufficiency branches
- [x] Goal progress engine (`calculate_goal_progress`) with calendar month interval and velocity feasibility status (`completed`, `on_track`, `at_risk`, `behind`)
- [x] Data contract compliance for `calculate_savings_rate` and `calculate_expense_ratio` (returns `Decimal | None`, correctly preserving `None` for zero/negative income)
- [x] Emergency fund evaluation (`calculate_emergency_fund`) categorizing coverage into 4 tiers (`critical`, `vulnerable`, `adequate`, `optimal`)
- [x] Affordability engine (`calculate_affordability`) evaluating liquid buffers, goal impacts, and 3-month surplus absorption
- [x] Multi-year comparative scenario simulation (`run_scenario`) with yearly trajectory points and net monetary delta
- [x] Backwards-compatible facade in `backend/app/financial/calculator.py`
- [x] Golden reference fixtures cross-checked against independent spreadsheet formulas
- [x] Property-based tests via Hypothesis (monotonicity in rate, monotonicity in time, lower bound guarantee, doubling time identity, scale invariance)
- [x] 99% test coverage on `app.financial` (39/39 tests passing, 108/108 passing across repository)
- [x] Full `mypy --strict` compliance (`[mypy-app.financial.*] strict = true` clean with 0 issues)
- [x] Comprehensive technical report written in `docs/phase-reports/phase-11.md`

---

## Phase 10 Checklist (Completed)
- [x] Model ladder benchmarked via time-based rolling-origin CV (Naive $7042.86 \to$ 3M MA $6187.60 \to$ Ridge $6566.33 \to$ GBDT Quantile $6016.76$ MAE)
- [x] Forecaster beats naive baseline by 34.3% relative error reduction on held-out cohort (MAE $6370.67$ vs Naive $9701.94$)
- [x] Uncertainty prediction intervals via multi-quantile regression ($\alpha \in \{0.08, 0.50, 0.92\}$) achieving $74.87\%$ empirical coverage (nominal $80\% \pm 10\%$ PASS)
- [x] Monotonic quantile ordering strictly guaranteed ($\hat{y}_{p10} \le \hat{y}_{p50} \le \hat{y}_{p90}$)
- [x] Deterministic 3-month moving average fallback for sparse history (< 2 months) with cultural festival calibration
- [x] Structured model registry in `ml/models_registry/` for all three models (Model A, Model B, Model C) with `current.json` pointers
- [x] Shadow evaluation and automated promotion quality gates implemented in `ml/registry/promotion.py`
- [x] Unified model serving layer in `backend/app/ml/inference.py` conforming to runtime `MLModel` protocol
- [x] Application startup initialization and hot-reload by version pointer
- [x] Graceful baseline fallback proven when artifacts are missing or corrupted (no unhandled exceptions)
- [x] Persistence service in `backend/app/services/ml_persistence.py` mapping model outputs to `predictions`, `behavior_profiles`, and `anomalies`
- [x] Diagnostic figures generated in `docs/ml/figures/model_c/` (`forecast_ladder_mae.png`, `rolling_origin_metrics.png`, `interval_coverage.png`, `residuals_distribution.png`)
- [x] Unit test suite (`backend/tests/unit/test_expense_forecaster.py`) passing 8/8 tests (69/69 tests passing across repository)
- [x] Model card and technical report completed in `docs/ml/model-c-report.md`

---

## Phase 9 Checklist (Completed)
- [x] Transaction-level robust Z-Score (median/MAD) implemented in `ml/models/transaction_anomaly.py`
- [x] Peer-group fallback on sparse history ($< 20$ txns) guaranteeing minimum group size $\ge 20$
- [x] Category-month spending detector implemented in `ml/models/category_month_anomaly.py`
- [x] Model ladder benchmark: Isolation Forest vs Local Outlier Factor (LOF) on $61,875$ records ($95.03\%$ concordance, IF $10\times$ faster)
- [x] Standardized output contract (`is_anomaly`, `anomaly_score`, `observed`, `baseline`, `deviation_pct`, `scope`, `explanation`) in `ml/models/anomaly_detector.py`
- [x] Alert budget policy strictly enforced ($\le 3$ alerts/user/month; $1.74$ primary, $1.39$ held-out)
- [x] Seasonality / cultural festival calibration (Dhaka 2026 calendar) reducing Eid false alarms by $46.4\%$
- [x] Analyst feedback service (`backend/app/services/anomaly_feedback.py`) supporting `confirmed` / `dismissed` actions and adaptive threshold offsets
- [x] Quarantined held-out seed cohort evaluation ($N=200$ users, $108,233$ txns): alert rate $1.39$/mo, FPR $0.0337$, AP $0.1408$
- [x] Publication-grade diagnostic figures generated in `docs/ml/figures/model_b/` (`pr_curves.png`, `per_type_recall.png`, `alert_rate_budget.png`, `festival_impact.png`)
- [x] Cryptographic artifact serialization (`ml/artifacts/anomaly_detector_v1.joblib` + metadata) with SHA-256 tamper verification
- [x] Backend singleton adapter in `backend/app/ml/anomaly.py`
- [x] Comprehensive unit test suite (`backend/tests/unit/test_anomaly_detector.py`) passing 10/10 tests (61/61 tests passing across repository)
- [x] Model card and technical report completed in `docs/ml/model-b-report.md`

---

## Phase 8 Checklist (Completed)
- [x] Model ladder benchmarked via 5-Fold Stratified Group CV on `user_id` (Rule Baseline $0.3001 \to$ Logistic Regression $0.6071 \to$ Random Forest $0.6647 \to$ HistGradientBoosting $0.6894$)
- [x] Probability calibration via `CalibratedClassifierCV(method='sigmoid')` achieving ECE = $0.0867$ ($< 0.10$)
- [x] Rigorous held-out seed cohort evaluation ($N=200$ users, $2,256$ months): Macro-F1 = $0.7148$, Accuracy = $74.47\%$, ROC-AUC OvR = $0.9427$
- [x] Acceptance criteria verified: beats rule baseline by $+138\%$ relative gain, strong but not suspiciously perfect ($< 0.99$, no target leakage)
- [x] Permutation feature importance and Tree SHAP explainability extracted (`cashout_frequency`, `rolling_sr_mean`, `discretionary_rate` as top drivers)
- [x] Non-judgmental, purely descriptive explainability factor generator implemented
- [x] Robustness checks passing: 100% scale invariance ($2\times$ scaling), 92% noise perturbation tolerance, cold start $< 2$ months returns `insufficient_data`, drifting users handled gracefully
- [x] Cryptographic artifact serialization (`ml/artifacts/behavior_classifier_v1.joblib` + metadata) with SHA-256 tamper-detection verification
- [x] Backend adapter (`backend/app/ml/behavior.py`) exposing verified singleton for FastAPI and workers
- [x] Diagnostic plots generated in `docs/ml/figures/model_a/` (confusion matrix, calibration curve, ROC-AUC, feature importance)
- [x] Unit test suite (`backend/tests/unit/test_behavior_classifier.py`) passing with 51/51 tests passing across repository
- [x] Comprehensive report in `docs/ml/model-a-report.md` completed and verified

---

---

## Phase 7 Checklist (Completed)
- [x] Single shared feature pipeline implemented in `ml/features/engine.py` and exposed via `backend/app/ml/features.py`
- [x] Strongly typed, versioned `MonthlyFeatureRecord` in `ml/features/schema.py` (`feature_schema_version = "v1.0.0"`)
- [x] All base monthly aggregates computed matching `design.md` §4.2 `monthly_features` schema
- [x] Rolling 3-month features implemented (rolling SR mean/std, savings consistency, expense mean/std, spending trend slope, category Shannon entropy, discretionary volatility, deficit months)
- [x] Asia/Dhaka (UTC+6) month-boundary partitioning guaranteed
- [x] Anti-double-counting verified: self cash-in excluded from income, transfer fees isolated, zero-income null savings rate
- [x] Incremental recomputation function (`engine.recompute_user_month_features`) with property testing against full batch recompute
- [x] Cohort backfill CLI (`python -m ml.features.cli backfill`) executed: 314,863 transactions across 600 users backfilled in 8.75s
- [x] Anti-leakage audit: 0 ground-truth columns present in feature store; null rates documented
- [x] 7 unit & property tests passing in `backend/tests/unit/test_feature_pipeline.py` (44/44 total repository tests passing)
- [x] `docs/phase-reports/phase-07.md` completed and verified

---

## Phase 6 Checklist (Completed)
- [x] Reproducible Jupyter Notebook in `ml/notebooks/eda.ipynb` (outputs cleared before commit)
- [x] Comprehensive EDA Report in `docs/data/eda.md` documenting 10 evidence-backed findings that influence ML design
- [x] 8 high-resolution statistical visualizations generated in `docs/data/figures/eda/`
- [x] Analysis of per-persona behavior, spending composition, volatility, seasonality, anomalies, cold start, correlations, and distributions
- [x] Anti-leakage quarantine and three-tier splitting strategy defined (user-level stratified, time-based sequential, held-out seed cohort)
- [x] Rule-based baselines implemented in `ml/models/baselines.py` (RuleBasedBehaviorClassifier, RobustZScoreAnomalyDetector, ExpenseForecasterBaseline)
- [x] Baseline benchmark evaluation pipeline implemented in `ml/evaluation/evaluate_baselines.py` reporting metrics on validation data
- [x] Comprehensive unit tests in `backend/tests/unit/test_ml_baselines.py` (37/37 total repository tests passing)
- [x] `docs/phase-reports/phase-06.md` completed and verified

---

## Phase 5 Checklist (Completed)
- [x] Primary training cohort ($N=600$ users, $314,863$ transactions, seed `42`) generated with 0 wallet invariant failures
- [x] Second held-out evaluation cohort ($N=200$ users, $108,233$ transactions, seed `1337`) generated and quarantined for later model validation
- [x] High-performance bulk database loader (`data/synthetic/loader.py`) with live asyncpg ingestion and offline `bulk_load.sql` generation
- [x] Statistical dataset validator (`ml/preprocessing/validate_dataset.py`) implementing all 10 domain checks and automated `--gate` enforcement
- [x] 10/10 checks verified in `docs/data/realism-report.md` (income skewness, savings rates, Engel's law $r=-0.71$, Eid seasonality, circadian rhythms, persona divergence, ledger solvency, fee calibration, anomaly rates, anti-leakage quarantine)
- [x] 7 high-resolution statistical visualizations generated in `docs/data/figures/`
- [x] Anti-leakage isolation verified: zero ground-truth columns present in `transactions` or `users` tables
- [x] Unit test suite updated (`backend/tests/unit/test_realism_validation.py`) with 31/31 passing tests
- [x] `docs/phase-reports/phase-05.md` completed and verified

---

## Phase 4 Checklist (Completed)
- [x] Generator architecture implemented under `data/synthetic/generator/` (`calendar.py`, `population.py`, `income.py`, `behavior.py`, `life_events.py`, `anomalies.py`, `wallet.py`, `writer.py`, `engine.py`)
- [x] Calendar engine configured in `data/synthetic/config/calendar.yaml` with Dhaka timezone, Friday/Saturday weekends, Ramadan/Eid dates, and bill cycles
- [x] Demographic generator (`population.py`) producing 600 realistic Bangladeshi identities with lognormal incomes across 8 occupations
- [x] Spending behavior engine implementing Engel's law, bill cycles, bazaar cadences, and separate MFS cash-out fee charges
- [x] Chronological wallet simulation guaranteeing strictly non-negative balances ($\ge 0$) and $100\%$ accounting invariant verification
- [x] Anomaly injection engine producing $2.50\%$ ground-truth anomalies (spikes, bursts, large cash-outs, odd hours)
- [x] Full dataset generated ($N=600$ users, $296,195$ transactions, $549$ goals, $2,326$ contributions, $7,402$ anomalies) in $19.46$ seconds
- [x] Parquet and CSV files exported to `data/exports/` (git-ignored)
- [x] Committed 5-user sample exported to `data/synthetic/sample/`
- [x] Unit, property, and determinism tests passing in `backend/tests/unit/test_synthetic_generator.py` (28/28 tests passing)
- [x] `docs/phase-reports/phase-04.md` written with distribution tables

---

## Phase 3 Checklist (Completed)
- [x] 17 SQLAlchemy 2.x declarative models in `backend/app/models/` (`NUMERIC(14,2)`, enums, composite keys)
- [x] Alembic migration `0001_initial_schema` (pgcrypto, citext, vector, CHECK constraints, idempotency constraint, HNSW index)
- [x] Alembic migration `0002_row_level_security` (ENABLE & FORCE RLS on all user tables with `app.user_id` session policy)
- [x] Database roles provisioned (`migrator`, `app_rw`, `worker_rw`, `readonly_analytics`) with `NOBYPASSRLS`
- [x] Cryptographic append-only protection on `audit_log` (`REVOKE UPDATE, DELETE, TRUNCATE`)
- [x] Defense-in-depth repository layer (`BaseRepository`, `UserRepository`, `TransactionRepository`, `GoalRepository`, `AuditLogRepository`)
- [x] Comprehensive Mermaid ERD exported to `docs/data/erd.md`
- [x] Automated unit and static Alembic SQL generation test coverage (`22 passed in 4.71s`)
- [x] `docs/phase-reports/phase-03.md` written and verified

---

## Phase 2 Checklist (Completed)
- [x] Complete metric definitions resolved in `docs/data/data-contract.md` (Dhaka timezone, cash-in/transfer/fee semantics)
- [x] 5+ comprehensive worked numeric examples tracing transactions to final metrics
- [x] 2-level taxonomy: 4 purposes (`necessity`, `savings_goal`, `discretionary`, `other`) and 25 Bangladeshi MFS categories
- [x] 6 behavioral archetypes + 1 mixed/drifting persona with exact parameter distributions
- [x] 8 socioeconomic occupation segments with BDT income percentiles and transition matrices
- [x] Quarantined ground-truth schema (`synthetic_ground_truth`) preventing ML data leakage
- [x] Phase 5 statistical realism quality metrics defined
- [x] Declarative YAML configs (`data/synthetic/config/*.yaml`) with unit-tested Pydantic models
- [x] `docs/phase-reports/phase-02.md` written with assumptions flagged for sign-off

---

## Phase 1 Checklist (Completed)
- [x] Monorepo directory structure created matching A6 layout
- [x] `.gitignore` and `.env.example` (zero secrets) configured
- [x] `docker-compose.yml` with postgres (pgvector), redis, backend-api, backend-worker, frontend, prometheus, grafana
- [x] Dev override pattern (`docker-compose.override.yml.example`) keeping ports private by default
- [x] FastAPI backend skeleton with `/health` and `/ready` endpoints
- [x] Settings via `pydantic-settings`
- [x] Structured JSON logging with request correlation IDs and log scrubbing
- [x] RFC 7807 Problem Details error handler
- [x] Tooling: `Makefile`, `ruff`, `mypy`, `pre-commit` (with gitleaks, nbstripout)
- [x] GitHub Actions CI workflow (lint, typecheck, test, secret scan, audit, docker build)
- [x] Multi-stage, non-root Dockerfiles for backend and frontend
- [x] `docs/DECISIONS.md` initialized with initial ADRs
- [x] `docs/phase-reports/phase-01.md` written and verified

---

## Known Gaps & Deferred Items
- Phase 5: Analytics, feature engineering, and ML pipeline (Monthly aggregations, LightGBM persona classifier, SHAP explainability).
- Phase 6: Core Financial API, authentication endpoints (Argon2id + JWT rotation), and outbox processing.
- Phase 7: Grounded Conversational AI & RAG Engine (pgvector embeddings, mock/live LLM interface).

---

## Decisions Log
See [DECISIONS.md](file:///d:/DIU%20Project/docs/DECISIONS.md) for detailed Architectural Decision Records.
