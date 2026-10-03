# Phase 06 Report — EDA & Data Quality Analysis

**Date:** 2026-10-03  
**Status:** Completed  
**Author:** Antigravity Autonomous Agent  

---

## 1. Executive Summary

Phase 6 performed exhaustive exploratory data analysis (EDA), data quality profiling, and baseline benchmarking across the primary synthetic transaction cohort ($N=600$ users, $314,863$ transactions) and quarantined evaluation cohort ($N=200$ users, $108,233$ transactions).

Key deliverables achieved:
1. **Jupyter Notebook (`ml/notebooks/eda.ipynb`)**:
   - Clean, reproducible, 18-cell notebook covering all analytical dimensions.
   - Outputs cleared prior to commit in compliance with repository hygiene rules.
2. **Comprehensive EDA Report (`docs/data/eda.md`)**:
   - Documents **10 evidence-backed quantitative findings** directly shaping feature selection, model architectures, loss functions, and cold-start fallbacks.
   - Accompanying 8 high-resolution figures in [`docs/data/figures/eda/`](file:///d:/DIU%20Project/docs/data/figures/eda/).
3. **Train / Validation / Test Splitting Protocol**:
   - **User-Level Stratified Split** (70% train / 30% val) for the behavior classifier to guarantee zero user leakage across monthly windows.
   - **Time-Based Sequential Split** (Months 1–9 train, Months 10–12 val) for expense forecasting to prevent temporal lookahead.
   - **Held-Out Test Set** (Quarantined seed 1337 cohort) reserved for final evaluation.
4. **Production-Grade Rule-Based Baselines (`ml/models/baselines.py`)**:
   - Threshold-based behavior classifier with cold-start detection.
   - Robust Z-score / MAD anomaly detector with peer-group fallback.
   - Naive and 3-month Simple Moving Average expense forecasters.
5. **Validation Benchmark Metrics (`ml/evaluation/evaluate_baselines.py`)**:
   - Behavior classifier: Accuracy $41.45\%$, Macro F1 $0.3233$.
   - Anomaly detector: Precision $7.37\%$, Recall $12.68\%$, F1 $0.0932$.
   - Forecasters: Naive sMAPE $14.57\%$, 3-Month SMA sMAPE $12.50\%$ (MAE BDT $5,831.16$).
6. **Unit Tests (`backend/tests/unit/test_ml_baselines.py`)**:
   - 6 new tests verifying cold-start handling, threshold rules, zero-MAD protection, peer fallback, and forecaster bounds. Total repository tests passing: **37 / 37**.

---

## 2. Quantitative Evidence Summary (10 Findings)

| # | Finding Name | Key Empirical Evidence | Core ML Design Impact |
|---|---|---|---|
| **1** | Persona Asymmetry in Savings Rates | `consistent_saver` $+31.2\%$, `tight_budgeter` $+2.4\%$ with $39.5\%$ deficit months | Feature store must track rolling 3-month mean savings rate AND deficit month count. |
| **2** | Engel's Law Necessity Scaling | Pearson $r = -0.73$ ($p < 10^{-90}$); Q1 necessity $84.2\%$ vs Q5 $48.6\%$ | Scale-invariant ratio features (`necessity_share`, `discretionary_share`) prevent income bias. |
| **3** | Occupational Volatility Asymmetry | Gig/freelance income CV $0.38 - 0.52$ vs formal workers $0.12 - 0.18$ | Forecaster must output prediction intervals (Quantile Regression $p_{10}, p_{50}, p_{90}$) rather than point estimates. |
| **4** | Bimodal Festival Seasonality | March volume $1.43\times$ mean (Eid-Fitr); May cash-out $+45\%$ (Eid-Adha Qurbani) | Forecaster must ingest cyclical month features and festival indicators to prevent moving average lag. |
| **5** | Circadian Commute Rhythms | $78.4\%$ transactions between 08:00–21:00; $<0.35\%$ overnight | Temporal anomaly feature (`hour_of_day`, `is_night_time`) flags nocturnal activity accurately. |
| **6** | Multi-Modal Anomaly Structure | $63.3\%$ micro-bursts, $19.3\%$ category spikes, $10.3\%$ cash-outs, $7.1\%$ odd hours | Univariate MAD catches only $12.7\%$ recall; justifies multi-variate Isolation Forest in Model B. |
| **7** | Cold-Start Data Sparsity | $15.9\%$ of (user, category) pairs have $< 10$ annual transactions; $>68\%$ in Month 1 | Mandatory peer-group fallback when $N < 10$; return `"insufficient_data"` if tenure $< 2$ months. |
| **8** | Feature Correlation Structure | High collinearity between `inflow` and `outflow` ($r=0.88$); `cashout_ratio` is orthogonal ($r=-0.18$) | `savings_rate`, `necessity_share`, and `cashout_ratio` form the orthogonal triad for classification. |
| **9** | Heavy-Tailed Monetary Amounts | Raw outflow skewness $+1.86$, kurtosis $+5.42$; log1p reduces skewness to $-0.12$ | All monetary features must be log-transformed (`log1p`) for linear or distance-based algorithms. |
| **10** | Persona Drift & Lifecycle Shifts | $58$ users ($9.7\%$) transition mid-year between months 6 and 9 | User-level split strictly required; classifier must output calibrated probabilities. |

---

## 3. Baseline Benchmark Performance on Validation Split

Evaluated against the $30\%$ validation split ($180$ users, $\sim 94,000$ transactions, months 10–12):

### 3.1 Behavior Classifier Baseline (`RuleBasedBehaviorClassifier`)
- **Accuracy:** $41.45\%$
- **Macro F1:** $0.3233$
- **Macro Precision:** $0.3004$
- **Macro Recall:** $0.4056$
- **Per-Class Breakdown:**
  - `cash_dominant_transactor`: Precision $0.54$, Recall $0.97$, F1 **$0.69$** (Strong)
  - `consistent_saver`: Precision $0.47$, Recall $0.63$, F1 **$0.54$** (Moderate)
  - `discretionary_spender`: Precision $0.21$, Recall $0.50$, F1 **$0.29$**
  - `tight_budgeter`: Precision $0.36$, Recall $0.26$, F1 **$0.30$**
  - `balanced_spender`: Precision $0.23$, Recall $0.08$, F1 **$0.12$**
  - `volatile_earner`: Precision $0.00$, Recall $0.00$, F1 **$0.00$**
- **Conclusion:** While heuristic thresholds capture dominant single-trait personas, they fail on overlapping boundaries. This establishes the baseline for machine learning models (LightGBM/XGBoost).

### 3.2 Anomaly Detector Baseline (`RobustZScoreAnomalyDetector`)
- **Precision:** $7.37\%$
- **Recall:** $12.68\%$
- **F1-Score:** $0.0932$
- **ROC-AUC:** $0.4562$
- **Conclusion:** Univariate MAD on single transaction amounts only detects large volume spikes. Multi-variate anomalies (frequency bursts, unusual night hours) require Isolation Forest and rolling feature aggregators.

### 3.3 Expense Forecaster Baselines (Months 10–12)
- **Naive Baseline (Persistence):**
  - MAE: BDT $6,865.96$
  - RMSE: BDT $11,537.96$
  - sMAPE: $14.57\%$
- **3-Month Simple Moving Average (SMA-3):**
  - MAE: **BDT $5,831.16$** ($-15.1\%$ error vs Naive)
  - RMSE: **BDT $9,368.21$** ($-18.8\%$ error vs Naive)
  - sMAPE: **$12.50\%$**
- **Conclusion:** SMA-3 sets the formal quantitative threshold that downstream regression models (Ridge, LightGBM) must surpass.

---

## 4. Verification & Testing

- `pytest backend/tests`: **37 / 37 passed** in 15.83s.
- `ruff check .`: 0 errors.
- `ruff format --check .`: 84 files compliant.
- `mypy --config-file mypy.ini backend/app data/synthetic ml`: 0 type errors across 65 source files.
- `infra/ci_secret_scan.py`: `[PASS]` 0 secrets found.

---

## 5. Next Steps

With empirical distributions, feature candidates, anti-leakage splitting strategies, and rule-based baselines validated, the platform is prepared to implement the core feature store and ML training pipelines in subsequent phases.
