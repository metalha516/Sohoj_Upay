# Phase 7 — Feature Engineering Pipeline Report

## Executive Summary

Phase 7 implements the unified, deterministic, testable feature engineering pipeline for the **Sohoj** platform. Conforming strictly to the **Single Source of Truth** principle, the feature calculation logic resides in `ml/features/engine.py` and is re-exported via `backend/app/ml/features.py`, ensuring that offline batch ML training and online backend application services execute the exact same feature transformations.

The pipeline computes all base monthly metrics defined in `design.md` §4.2 as well as rolling 3-month behavioral signals, versioned under `FeatureSchema` `v1.0.0`.

---

## Architecture & Code Organization

```
ml/features/
├── __init__.py          # Package exports: MonthlyFeatureEngine, MonthlyFeatureRecord, etc.
├── schema.py            # Typed Pydantic MonthlyFeatureRecord with version v1.0.0
├── engine.py            # Deterministic aggregation engine & Asia/Dhaka timezone calendar
└── cli.py               # Backfill & incremental recompute CLI with anti-leakage auditing

backend/app/ml/
└── features.py          # Unified adapter re-exporting ml.features for backend serving
```

### 1. Dual-Mode Execution Architecture
- **Online Serving:** `MonthlyFeatureEngine.recompute_user_month_features()` executes incremental updates for single `(user, month)` pairs or downstream rolling windows when a user records a new transaction or backdated entry.
- **Offline Batch Processing:** `MonthlyFeatureEngine.compute_user_features()` and `python -m ml.features.cli backfill` process large cohorts in parallel across partitioned datasets.

---

## Implemented Feature Schema (`v1.0.0`)

### Base Monthly Features (`monthly_features` Table)
| Feature Name | Type | Contract & Derivation | Null Condition |
|---|---|---|---|
| `user_id` | `UUID` | Unique account identifier | Non-null |
| `month` | `date` | First calendar day of the month in `Asia/Dhaka` | Non-null |
| `income` | `Decimal(14,2)` | Inflows (salary, freelance, remittances, family support). `cash_in_self` excluded. | 0.00 if no inflows |
| `expense` | `Decimal(14,2)` | Outflows (necessity, discretionary, other) + cash-out/transfer fees. | 0.00 if no outflows |
| `savings` | `Decimal(14,2)` | Transfers or cash-outs tagged `purpose = savings_goal`. | 0.00 if no savings |
| `savings_rate` | `Decimal(6,4)` | $\frac{\text{Savings}}{\text{Income}}$, rounded to 4 decimals. | `null` when $\text{Income} \le 0$ |
| `necessity_expense` | `Decimal(14,2)` | Outflows with `purpose = necessity` + fees. | Non-null |
| `discretionary_expense` | `Decimal(14,2)` | Outflows with `purpose = discretionary`. | Non-null |
| `necessity_rate` | `Decimal(6,4)` | $\frac{\text{Necessity Expense}}{\text{Expense}}$. | `null` when $\text{Expense} \le 0$ |
| `discretionary_rate` | `Decimal(6,4)` | $\frac{\text{Discretionary Expense}}{\text{Expense}}$. | `null` when $\text{Expense} \le 0$ |
| `txn_count` | `int` | Total transaction events in month. | Non-null |
| `cashout_count` | `int` | Number of MFS agent cash-out events. | Non-null |
| `avg_txn` | `Decimal(14,2)` | Mean transaction volume. | `null` if 0 txns |
| `median_txn` | `Decimal(14,2)` | Median transaction volume. | `null` if 0 txns |
| `expense_variance` | `Decimal(14,2)` | Sample variance ($ddof=1$) of expense transactions. | `null` if $< 2$ expense txns |
| `spending_growth` | `Decimal(6,4)` | $\frac{\text{Expense}_M - \text{Expense}_{M-1}}{\text{Expense}_{M-1}}$. | `null` for month 1 |
| `income_expense_ratio` | `Decimal(6,4)` | $\frac{\text{Income}}{\text{Expense}}$. | `null` when $\text{Expense} \le 0$ |
| `category_breakdown` | `dict[str, float]` | JSON breakdown of expenditure by category. | Non-null |

### Rolling 3-Month Features
| Feature Name | Formula / Description | ML Utility |
|---|---|---|
| `rolling_savings_rate_3m_mean` | 3-month moving average of `savings_rate` | Smooth savings discipline measure |
| `rolling_savings_rate_3m_std` | Sample standard deviation of 3-month `savings_rate` | Savings consistency / volatility |
| `savings_consistency` | $\max(0, 1 - \text{rolling\_savings\_rate\_std})$ | Behavioral stability index |
| `rolling_expense_3m_mean` | 3-month moving average of monthly expenses | Baseline expense anchoring |
| `rolling_expense_3m_std` | 3-month moving standard deviation of monthly expenses | Expense volatility metric |
| `spending_trend_3m` | Linear regression slope across 3-month expense totals | Trend trajectory (growing / shrinking) |
| `category_entropy_3m` | Shannon entropy: $H = -\sum p_i \ln(p_i)$ over 3-month categories | Expenditure diversification vs concentration |
| `discretionary_volatility_3m` | Standard deviation of discretionary share over 3 months | Impulsive lifestyle indicator |
| `deficit_months_3m` | Count of months where $\text{Income} - \text{Expense} - \text{Savings} < 0$ | Financial distress warning |

---

## Backfill Audit & Performance

The cohort backfill CLI was executed against the primary dataset ($N=600$ users, $314,863$ transactions):

```powershell
python -m ml.features.cli backfill --data-dir data/exports --output-dir data/exports
```

### Execution Metrics
- **Total Users:** 600
- **Total Transactions:** 314,863
- **Total Monthly Records:** 7,200 ($600 \times 12$ months)
- **Runtime:** 8.75 seconds (~822 monthly records / sec)
- **Output Files:**
  - `data/exports/monthly_features.parquet` (7,200 rows)
  - `data/exports/monthly_features.csv`

### Feature Null Rates Audit
| Feature | Null Rate | Rationale & Invariant Check |
|---|---|---|
| `user_id` | **0.00%** | Key column |
| `month` | **0.00%** | Key column |
| `feature_schema_version` | **0.00%** | Metadata tag (`v1.0.0`) |
| `income` | **0.00%** | Zero-filled when no income |
| `expense` | **0.00%** | Zero-filled when no expense |
| `savings` | **0.00%** | Zero-filled when no savings |
| `savings_rate` | **2.68%** | Expected: Users with ৳0 income in specific months (e.g. students, gig workers) have null savings rate per Data Contract §1.2 |
| `necessity_expense` | **0.00%** | Zero-filled |
| `discretionary_expense` | **0.00%** | Zero-filled |
| `necessity_rate` | **0.00%** | All 7,200 user-months had expenses |
| `discretionary_rate` | **0.00%** | All 7,200 user-months had expenses |
| `txn_count` | **0.00%** | Discrete count |
| `cashout_count` | **0.00%** | Discrete count |
| `avg_txn` | **0.00%** | Non-null across active user months |
| `median_txn` | **0.00%** | Non-null across active user months |
| `expense_variance` | **0.00%** | Computed whenever $\ge 2$ expense txns exist |
| `spending_growth` | **8.33%** | Exactly $\frac{1}{12}$ months: Month 1 of each user's history has no prior month to calculate growth |
| `income_expense_ratio` | **0.00%** | Computed for all user-months |
| `category_breakdown` | **0.00%** | Serialized JSON dictionary |
| `rolling_savings_rate_3m_mean` | **0.47%** | Rare cases where all months in the 3-month window had ৳0 income |
| `rolling_savings_rate_3m_std` | **0.47%** | Matches null condition above |
| `savings_consistency` | **0.47%** | Matches null condition above |
| `rolling_expense_3m_mean` | **0.00%** | Always available |
| `rolling_expense_3m_std` | **0.00%** | Always available |
| `spending_trend_3m` | **0.00%** | Always available |
| `category_entropy_3m` | **0.00%** | Always available |
| `discretionary_volatility_3m` | **0.00%** | Always available |
| `deficit_months_3m` | **0.00%** | Always available |

### Anti-Leakage Audit
The automated anti-leakage validator checked all exported columns against forbidden ground-truth targets:
- Forbidden: `true_persona`, `true_occupation`, `is_anomaly`, `anomaly_type`, `severity_score`, `is_drifting`, `secondary_persona`.
- **Audit Result:** **PASSED** (0 forbidden columns present).

---

## Verification & Test Results

The full test suite (`backend/tests/unit/test_feature_pipeline.py`) covers 7 distinct scenarios:

1. **Worked Example 1 Reconciliation:** Reconciles the Corporate Executive persona from `docs/data/data-contract.md` §1.3 with hand-calculated metrics:
   - Income: ৳65,000.00
   - Expense: ৳35,970.00
   - Savings: ৳15,000.00
   - Savings Rate: 23.08%
   - Necessity Expense: ৳32,570.00
   - Discretionary Expense: ৳3,400.00
   - *Status:* **PASS**
2. **Asia/Dhaka Timezone Boundary:** Validates that transactions close to UTC midnight (e.g., 23:59 UTC+6 vs 00:01 UTC+6) partition cleanly into January vs February.
   - *Status:* **PASS**
3. **Anti-Double-Counting:** Validates that `cash_in_self` is ignored as income, and peer transfers without savings intent are excluded from expenses.
   - *Status:* **PASS**
4. **Zero-Income Handling:** Validates that zero income strictly sets `savings_rate = None`.
   - *Status:* **PASS**
5. **Incremental vs Full Recompute (Property Test):** Validates that `engine.recompute_user_month_features()` on an affected month produces the identical result as `engine.compute_user_features()` across the full history.
   - *Status:* **PASS**
6. **Late-Arriving Transaction Updates:** Validates that inserting a transaction into an earlier month properly recomputes that month's metrics and updates subsequent rolling windows.
   - *Status:* **PASS**
7. **Schema Versioning & Anti-Leakage:** Asserts schema version tag `v1.0.0` and absence of ground-truth leakage fields.
   - *Status:* **PASS**

### Test Suite Execution Summary
```
====================== 44 passed, 59 warnings in 13.72s =======================
```
- **Ruff Lint:** 0 errors
- **Ruff Format:** 95 files formatted cleanly
- **Mypy Typecheck:** 70 source files checked, 0 errors
- **Secret Scan:** 0 credentials found
