# Phase 14 Report: ML, Forecast & Simulation APIs; Anomaly Pipeline Integration

## Executive Summary
Phase 14 operationalizes the machine learning models developed in Phases 8–10 (Behavior Classification, Anomaly Detection, Expense Forecasting) and the deterministic Financial Engine from Phase 11 into production-ready, secure, and low-latency RESTful APIs. It establishes the end-to-end intelligence loop: new transaction inputs trigger outbox events, background workers evaluate anomaly scoring, insights and recommendations are persisted with traceable audit metadata, and users can query behavior profiles, forecasts with quantile intervals, and run financial simulations with exact cent precision.

---

## 1. Architecture & Component Design

```
+---------------------------------------------------------------------------------------------------+
|                                          FastAPI Gateway                                          |
|  +--------------------+  +--------------------+  +--------------------+  +---------------------+  |
|  |    /behavior/*     |  |    /anomalies/*    |  |    /forecast/*     |  |     /simulate/*     |  |
|  +---------+----------+  +---------+----------+  +---------+----------+  +----------+----------+  |
+------------|-----------------------|-----------------------|------------------------|-------------+
             |                       |                       |                        |
             v                       v                       v                        |
+---------------------------------------------------------------+                     |
|                           MLService                           |                     |
|  - Debounced profile refresh (<= 1 per 15 min per user)       |                     |
|  - Cold-start guard (< 2 months -> RFC 7807 INSUFFICIENT_DATA)|                     |
|  - Model A (LightGBM) Archetype Classification + Factors      |                     |
|  - Model B (Median/MAD + Peer Fallback) Anomaly Detection     |                     |
|  - Model C (Quantile Regressor p10/p50/p90) Expense Forecast  |                     |
|  - Rule-based Baseline Fallback (3M Moving Average)           |                     |
|  - Nightly Batch Job orchestration                            |                     |
+----------------+-------------------+--------------------------+                     |
                 |                   |                                                |
                 v                   v                                                v
   +-----------------------+   +------------------------+             +-------------------------------+
   | Anomaly / Rec Repos   |   | Feature / Profile Repo |             |       SimulationService       |
   | - anomalies           |   | - monthly_features     |             | Pure Financial Engine wrapper |
   | - ai_recommendations  |   | - behavior_profiles    |             | - FV, Doubling, Goal, Scenarios|
   | - predictions         |   +------------------------+             | - Decimal ROUND_HALF_UP       |
   +-----------------------+                                          +-------------------------------+
```

### 1.1 `MLService`
Located at `backend/app/services/ml_service.py`:
- **Model A (Behavior Classifier):** Orchestrates behavior archetype prediction (`balanced_spender`, `consistent_saver`, `tight_budgeter`, `discretionary_spender`, `cash_dominant_transactor`, `volatile_earner`) along with calibrated confidence score and top explainability factors.
- **Debounced Refresh:** Implements a 15-minute throttle per user. If a valid behavior profile exists and was computed within the last 15 minutes, the cached profile is returned immediately without invoking model re-inference.
- **Cold-Start Enforcement:** If user tenure is fewer than 2 distinct monthly feature records, the service raises `InsufficientDataError` returning RFC 7807 `422 Unprocessable Entity` with `code="INSUFFICIENT_DATA"` and contextual guidance.
- **Model B (Anomaly Detection):** Evaluates single transactions using median/MAD metrics with peer-group fallback when user history has fewer than 5 transactions in a category. Generates `is_anomaly`, `anomaly_score`, `observed_value`, `baseline_value`, and structured JSON explanations.
- **Insight & Recommendation Generation:** Rule-templated actionable insights without LLM nondeterminism or latency overhead. Recommends target actions and stores deterministic `source_refs` (e.g., `["anomaly:c2a4f..."]`, `["feature:discretionary_share"]`).
- **Model C (Expense & Savings Forecaster):** Provides next-month forecasts with 10th, 50th, and 90th percentile bounds, historical trends, and savings projections. Gracefully falls back to a 3-month moving average baseline if ML model artifacts are missing or uncalibrated.
- **Nightly Batch Processing:** `run_nightly_batch_job()` iterates across all active platform users, evaluates historical months, runs batch feature updates, and commits refreshed behavior profiles and predictions.

### 1.2 `SimulationService`
Located at `backend/app/services/simulation_service.py`:
- Pure wrapper around `backend/app/financial/` deterministic engine.
- Enforces strict `Decimal` arithmetic with `ROUND_HALF_UP` formatting.
- Includes mandatory `AssumptionsBlock` and `disclaimer_code="PROJECTION_NOT_GUARANTEED"` on all projections.
- Supports:
  1. `POST /api/v1/simulate/growth`: Compound interest growth curves across monthly/annual compounding frequencies.
  2. `POST /api/v1/simulate/goal`: Required monthly savings and timeline calculations to hit financial milestones.
  3. `POST /api/v1/simulate/doubling`: Rule of 72 approximation alongside exact compound interest doubling periods.
  4. `POST /api/v1/simulate/scenario`: Multi-year financial trajectory forecasting under parameterized income/expense/investment return shocks.

### 1.3 Asynchronous Outbox Worker Integration
Located at `backend/app/worker/outbox_worker.py`:
- Listens for `transaction.created` events emitted during transaction writes.
- Computes monthly features for the affected month.
- Evaluates the transaction against Model B anomaly detection.
- Automatically persists detected anomalies to `anomalies` table and generates linked recommendations in `ai_recommendations`.

---

## 2. API Contract & Endpoints Summary

| Endpoint | Method | Description | Key Query / Payload Params | Response Summary |
|---|---|---|---|---|
| `/api/v1/behavior/profile` | GET | Current behavior profile | None | Archetype, confidence, top factors, debounced cache status |
| `/api/v1/behavior/insights` | GET | Algorithmic insights | `limit` (default 5) | List of actionable recommendations with priority and category |
| `/api/v1/anomalies` | GET | List spending anomalies | `status`, `scope`, `limit` | List of detected anomalies with score, observed, baseline, explanation |
| `/api/v1/anomalies/{anomaly_id}` | PATCH | Submit feedback | `status` (`dismissed` / `confirmed`) | Updated anomaly record; 404 on cross-tenant access |
| `/api/v1/forecast/expenses` | GET | Next-month expense forecast | None | Point estimate (p50), uncertainty interval (p10, p90), confidence, assumptions |
| `/api/v1/forecast/savings` | GET | Projected savings forecast | None | Projected savings, savings rate, confidence, assumptions |
| `/api/v1/simulate/growth` | POST | Future value projection | `principal`, `monthly_contribution`, `annual_rate_pct`, `years`, `compounding_frequency` | Final balance, total contributions, total interest, yearly breakdown table |
| `/api/v1/simulate/goal` | POST | Milestone savings planner | `target_amount`, `current_savings`, `annual_rate_pct`, `time_horizon_months` | Required monthly saving, feasibility assessment |
| `/api/v1/simulate/doubling` | POST | Capital doubling time | `annual_rate_pct`, `compounding_frequency` | Exact doubling years, Rule of 72 comparison |
| `/api/v1/simulate/scenario` | POST | Multi-year financial model | `annual_income`, `annual_expenses`, `current_net_worth`, `years`, overrides | Baseline vs simulated trajectories with difference analysis |

---

## 3. Latency Benchmark & Performance Verification

An automated performance benchmark (`backend/tests/integration/test_dashboard_latency.py`) was executed across 100 sequential requests against the core `/api/v1/dashboard` endpoint with multi-tenant data, cache invalidation cycles, and background feature lookups.

### Benchmark Results
- **Sample Size:** 100 requests
- **Min Latency:** 11.23 ms
- **Median ($p50$):** 14.83 ms
- **$p90$ Latency:** 21.13 ms
- **$p95$ Latency:** **33.44 ms**
- **$p99$ Latency:** 46.01 ms
- **Max Latency:** 52.88 ms
- **Target SLA:** $p95 < 500\text{ ms}$
- **Outcome:** **Exceeded SLA by ~15x** ($33.44\text{ ms} \ll 500\text{ ms}$).

---

## 4. Security & Compliance Verification

1. **RFC 7807 Problem Details:**
   Cold-start requests return HTTP 422 with `application/problem+json`:
   ```json
   {
     "type": "https://sohoj.app/errors/insufficient-data",
     "title": "Insufficient Data",
     "status": 422,
     "detail": "At least 2 completed months of transaction history are required to classify financial behavior. Current history: 1 month(s).",
     "code": "INSUFFICIENT_DATA",
     "guidance": "Continue recording daily transactions across at least 2 consecutive calendar months to unlock behavioral profiling."
   }
   ```
2. **OWASP ASVS Tenant Isolation (RLS / AuthZ):**
   - OpenAPI-driven authorization matrix (`backend/tests/security/test_authz_matrix.py`) verifies that user B attempting to modify or view user A's anomaly via `PATCH /api/v1/anomalies/{anomaly_id}` yields strict `404 Not Found` (never 200, 403, or data leak).
   - 8 distinct parameterized route combinations tested and verified.
3. **Property-Based API Fuzzing:**
   - Schemathesis property tests (`test_openapi_schemathesis.py`) tested all mounted endpoints under arbitrary payload perturbations with 0 server errors (zero 5xx).

---

## 5. Test Suite & Code Quality Metrics

| Category | Suite | Tests | Result |
|---|---|---|---|
| **Integration** | `test_ml_and_simulation_apis.py` | 8 | PASSED |
| **Integration** | `test_dashboard_latency.py` | 1 | PASSED ($p95 = 33.44\text{ ms}$) |
| **Integration** | `test_goals_financial_engine.py` | 1 | PASSED |
| **Integration** | `test_transactions_outbox_dashboard.py` | 5 | PASSED |
| **Security** | `test_auth_security.py` | 16 | PASSED |
| **Security** | `test_authz_matrix.py` | 2 | PASSED |
| **Security** | `test_log_hygiene.py` | 2 | PASSED |
| **Security** | `test_openapi_schemathesis.py` | 27 | PASSED |
| **Unit** | `test_anomaly_detector.py` | 10 | PASSED |
| **Unit** | `test_behavior_classifier.py` | 7 | PASSED |
| **Unit** | `test_errors.py` | 2 | PASSED |
| **Unit** | `test_expense_forecaster.py` | 8 | PASSED |
| **Unit** | `test_feature_pipeline.py` | 7 | PASSED |
| **Unit** | `test_financial.py` | 2 | PASSED |
| **Unit** | `test_financial_engine.py` | 39 | PASSED |
| **Unit** | `test_health.py` | 3 | PASSED |
| **Unit** | `test_logging.py` | 2 | PASSED |
| **Unit** | `test_ml_baselines.py` | 6 | PASSED |
| **Unit** | `test_models.py` | 4 | PASSED |
| **Unit** | `test_realism_validation.py` | 3 | PASSED |
| **Unit** | `test_repositories.py` | 4 | PASSED |
| **Unit** | `test_rls_sql.py` | 1 | PASSED |
| **Unit** | `test_synthetic_config.py` | 5 | PASSED |
| **Unit** | `test_synthetic_generator.py` | 5 | PASSED |
| **Total Test Suite** | `pytest backend/tests/` | **170** | **170 PASSED (100%)** |

### Static Analysis
- **Mypy Strict:** 0 issues found across 131 source files (`mypy --config-file mypy.ini backend/app data/synthetic ml`).
- **Ruff Linter:** 100% clean (`ruff check backend ml data`).
- **Ruff Formatter:** 100% formatted (`ruff format --check backend ml data`).
