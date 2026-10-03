# Phase 05 Report — Data Generation Run, Load & Realism Validation

**Date:** 2026-10-03  
**Status:** Completed  
**Author:** Antigravity Autonomous Agent  

---

## 1. Executive Summary

Phase 5 verified and certified the realism, statistical distributions, and architectural integrity of the synthetic Mobile Financial Services (MFS) transaction cohorts before any machine learning modeling is initiated.

Key milestones achieved:
1. **Primary & Held-Out Cohorts Generated**:
   - **Primary Training Cohort** ($N=600$ users, seed `42`): $314,863$ transactions, $549$ financial goals, $2,315$ contributions, and $7,800$ ground-truth anomalies ($2.48\%$).
   - **Held-Out Evaluation Cohort** ($N=200$ users, seed `1337`): $108,233$ transactions, $187$ financial goals, $622$ contributions, and $2,720$ ground-truth anomalies ($2.51\%$). This dataset is quarantined strictly for final model evaluation in later phases.
2. **PostgreSQL Bulk Loader (`data/synthetic/loader.py`)**:
   - High-throughput asynchronous streaming loader using `asyncpg.copy_records_to_table`.
   - Automatic fallback generating offline, production-grade `bulk_load.sql` utilizing PostgreSQL `\copy` statements respecting topological foreign-key ordering (`users` $\to$ `synthetic_user_ground_truth` $\to$ `financial_goals` $\to$ `transactions` $\to$ `goal_contributions` $\to$ `synthetic_transaction_ground_truth`).
3. **Automated Statistical Realism Validator (`ml/preprocessing/validate_dataset.py`)**:
   - Exhaustive 10-point audit verifying socioeconomic income distributions, savings-rate dispersion, Engel's law elasticity, cultural seasonality, circadian activity, persona divergence, ledger solvency, fee calibration, anomaly rates, and anti-leakage quarantine.
   - Comprehensive `--gate` CLI flag exiting non-zero if any metric violates domain bounds.
   - Exported Markdown audit report to [`docs/data/realism-report.md`](file:///d:/DIU%20Project/docs/data/realism-report.md) accompanied by 7 high-resolution figures in [`docs/data/figures/`](file:///d:/DIU%20Project/docs/data/figures/).

---

## 2. Statistical Realism Audit Scorecard

All 10 checks evaluated against the primary cohort passed strict mathematical and domain bounds:

| Check ID | Statistical Metric Evaluated | Threshold / Specification | Result | Observed Cohort Metric |
|---|---|---|---|---|
| `CHECK_01_INCOME_DIST` | Income Distribution & Skewness | Skewness $> 0.40$, Min $\ge 3,500$, Max $\le 250,000$ | **PASS** | Skewness $= 1.86$, Min $=$ BDT $4,492$, Max $=$ BDT $175,000$ |
| `CHECK_02_SAVINGS_RATE` | Savings-Rate Dispersion | Deficit $> 5\%$, Surplus $> 15\%$, Dominant $< 70\%$ | **PASS** | Deficit months $= 39.5\%$, Surplus months $= 59.3\%$ |
| `CHECK_03_ENGELS_LAW` | Engel's Law Necessity Scaling | Pearson $r < -0.20$, $p < 0.01$ | **PASS** | Pearson $r = -0.71$, $p = 1.57 \times 10^{-94}$ |
| `CHECK_04_SEASONALITY` | Cultural Festival Outflows | March $> 1.15\times$, May $> 1.10\times$ vs Baseline | **PASS** | March (Eid-Fitr) $= 1.35\times$, May (Eid-Adha) $= 1.26\times$ |
| `CHECK_05_TEMPORAL` | Circadian Rhythms & Commute | Daytime/Evening to Midnight Ratio $> 3.0\times$ | **PASS** | Peak-to-trough ratio $= 237.8\times$ |
| `CHECK_06_TXNS_PER_USER` | Transaction Activity & Density | Min $\ge 80$, Zero-Txn Users $= 0$ | **PASS** | Min $= 392$, Median $= 496$, Zero-txn users $= 0$ |
| `CHECK_07_PERSONA_SHARES` | Persona Spending Divergence | Discretionary Dining $> 1.5\times$ Tight Budgeter | **PASS** | Discretionary dining $= 17.7\%$ vs Tight budgeter $= 5.6\%$ ($3.16\times$) |
| `CHECK_08_LEDGER_INVARIANTS` | Ledger Solvency & Fee Calibration | 0 Negative, 0 Dups, Fee $1.49\% - 1.85\%$ | **PASS** | 0 negative, 0 dups, 0 future ts, Effective fee $= 1.64\%$ |
| `CHECK_09_NOISE_ANOMALIES` | Anomaly & Noise Calibration | Anomalies $2.0\% - 3.2\%$, "Other" $4.0\% - 10.0\%$ | **PASS** | Anomaly rate $= 2.48\%$, Noise share $= 6.06\%$ |
| `CHECK_10_LEAKAGE` | Ground-Truth Leakage Isolation | 0 target columns in ledger tables | **PASS** | Zero target columns in `transactions` or `users` |

---

## 3. Detailed Realism Findings & Visualizations

### 3.1 Income Distribution per Occupation (`CHECK_01_INCOME_DIST`)
- **Figure:** [`docs/data/figures/01_income_by_occupation.png`](file:///d:/DIU%20Project/docs/data/figures/01_income_by_occupation.png)
- **Observations:** Income displays clear right-skewed lognormal characteristics ($+1.86$ skewness). Garment workers cluster tightly between BDT $8,000$ and BDT $15,000$, whereas private sector professionals and corporate government employees extend smoothly up to BDT $175,000$.

### 3.2 Savings-Rate Dispersion (`CHECK_02_SAVINGS_RATE`)
- **Figure:** [`docs/data/figures/02_savings_rate_distribution.png`](file:///d:/DIU%20Project/docs/data/figures/02_savings_rate_distribution.png)
- **Observations:** Realistic two-sided distribution. $39.5\%$ of user-months experience net deficits (driven by festival splurges, medical emergencies, or income volatility), while $59.3\%$ generate monthly surpluses. Neither sign dominates ($<70\%$ constraint satisfied).

### 3.3 Engel's Law Elasticity (`CHECK_03_ENGELS_LAW`)
- **Figure:** [`docs/data/figures/03_engels_law_necessity_vs_income.png`](file:///d:/DIU%20Project/docs/data/figures/03_engels_law_necessity_vs_income.png)
- **Observations:** Strongly negative correlation ($r = -0.71, p < 10^{-90}$). Low-income users dedicate $75\% - 90\%$ of expenditures to absolute necessities (bazaar staples, mess rent, utilities), whereas high-income earners dedicate less than $55\%$ to necessities and expand discretionary dining, e-commerce, and entertainment.

### 3.4 Calendar & Festival Seasonality (`CHECK_04_SEASONALITY`)
- **Figure:** [`docs/data/figures/04_monthly_seasonality.png`](file:///d:/DIU%20Project/docs/data/figures/04_monthly_seasonality.png)
- **Observations:** Distinct macroeconomic spikes occur during March ($1.35\times$ baseline volume for Ramadan / pre-Eid-ul-Fitr apparel and gift shopping) and May ($1.26\times$ baseline volume for Eid-ul-Adha Qurbani livestock purchases and cattle market agent cash-outs).

### 3.5 Circadian & Payday Clustering (`CHECK_05_TEMPORAL`)
- **Figure:** [`docs/data/figures/05_day_and_hour_patterns.png`](file:///d:/DIU%20Project/docs/data/figures/05_day_and_hour_patterns.png)
- **Observations:** Circadian activity peaks during morning commutes ($08:00 - 10:00$) and evening leisure ($18:00 - 21:00$), dropping to near-zero between $01:00$ and $05:00$. Income credits exhibit sharp clustering on salary disbursement days ($1^{\text{st}} - 7^{\text{th}}$ of the month).

### 3.6 Transaction Frequency & Activity Density (`CHECK_06_TXNS_PER_USER`)
- **Figure:** [`docs/data/figures/06_transactions_per_user.png`](file:///d:/DIU%20Project/docs/data/figures/06_transactions_per_user.png)
- **Observations:** $100\%$ of users possess substantial transactional histories (minimum $392$ events, median $496$ events annually), ensuring sufficient density for recurrent neural networks and temporal feature aggregators.

### 3.7 Persona Composition Divergence (`CHECK_07_PERSONA_SHARES`)
- **Figure:** [`docs/data/figures/07_category_shares_by_persona.png`](file:///d:/DIU%20Project/docs/data/figures/07_category_shares_by_persona.png)
- **Observations:** Discretionary spenders dedicate $17.7\%$ of total expense volume to dining and restaurant orders, while tight budgeters spend only $5.6\%$. Cash-dominant transactors prioritize cash-out transfers ($>70\%$ of outflows).

### 3.8 Zero-Leakage Quarantine Verification (`CHECK_10_LEAKAGE`)
- Physical separation of target variables confirmed:
  - `transactions` and `users` tables contain zero ground-truth target columns (`true_persona`, `true_occupation`, `is_anomaly`, `anomaly_type`, `severity_score`).
  - Target labels reside strictly in `synthetic_user_ground_truth` and `synthetic_transaction_ground_truth`.

---

## 4. Verification & Testing

1. **Unit & Property Tests**:
   - `backend/tests/unit/test_synthetic_generator.py` (28 passed)
   - `backend/tests/unit/test_realism_validation.py` (3 passed: bulk loader SQL generation, full 10-check realism suite, anti-leakage injection detection)
   - Total unit tests passing: **31 / 31** in 15.72s.
2. **Static Quality & Security**:
   - `ruff check .` $\to$ 0 errors
   - `ruff format --check .` $\to$ 80 files compliant
   - `mypy --config-file mypy.ini backend/app data/synthetic ml` $\to$ 0 issues in 58 files
   - `infra/ci_secret_scan.py` $\to$ 0 secrets found
3. **Automated Realism Gate CLI**:
   - Command: `python -m ml.preprocessing.validate_dataset --data-dir data/exports --gate`
   - Exit Code: `0` (CERTIFIED FOR FEATURE ENGINEERING)

---

## 5. Next Steps (Phase 6 Transition)

With dataset realism statistically certified and zero target leakage verified, the platform is ready for **Phase 6: Core Financial API, Services & Outbox Processing**:
- Pure deterministic Financial Calculation Engine (`Decimal`, no DB/ML dependencies).
- User and Transaction CRUD endpoints with forced RLS and Argon2id/JWT authentication.
- Transactional outbox event publisher with Redis Streams.
