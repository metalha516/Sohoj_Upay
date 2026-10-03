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
| **Phase 12** | Grounded Conversational AI & RAG Engine | Pending | - |
| **Phase 13** | Next.js Frontend Dashboard & Coach Interface | Pending | - |

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
