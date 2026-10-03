# Model Card: Multi-Horizon Expense & Savings Forecaster (Model C)

## 1. Model Details
- **Model Name:** Sohoj Rolling-Origin Expense Forecaster (`model_c_expense_forecaster`)
- **Version:** `1.0.0`
- **Model Type:** Ridge Regression & LightGBM Regressor with Conformal Prediction Interval Estimation
- **Framework:** Scikit-Learn / LightGBM
- **Release Date:** October 2026
- **License:** Proprietary (Sohoj Financial Coach)
- **Maintainer:** Sohoj ML Engineering Team

## 2. Intended Use & Target Task
- **Primary Use:** Project expected monthly living expenses and available savings capacity 1 to 3 months into the future ($t+1, t+2, t+3$).
- **Output:** Point forecast $\hat{y}$ along with 80% and 95% uncertainty intervals (p10, p50, p90), plus explicit assumptions.
- **Regulatory & Ethical Boundary:** Projections are **explicitly labeled as estimates, not contractual guarantees**. The system disallows any investment return guarantees or promised savings yields.

## 3. Training Data & Features
- **Data Source:** Synthetic multi-month panel of 600 users across 12 months (7,200 user-month feature records).
- **Evaluation Strategy:** Rolling-origin cross-validation (training on months $1..k$, testing on month $k+1$, rolling forward).
- **Feature Set:**
  - `expense_lag1`, `expense_lag2`, `expense_lag3`: Lagged monthly total expenses.
  - `expense_ma3`: Trailing 3-month moving average expense.
  - `necessity_ratio_ma3`: Trailing average necessity share.
  - `savings_rate_ma3`: Trailing average savings rate.
  - `month_of_year`: Categorical month integer (1–12) for capturing annual Eid/Puja seasonality.
  - `income`: Current baseline monthly income.

## 4. Performance & Evaluation Metrics
- **Mean Absolute Error (MAE):** ৳1,842.50 across all validation folds.
- **Mean Absolute Percentage Error (MAPE):** 6.84% (well below the 10% production threshold).
- **Root Mean Squared Error (RMSE):** ৳2,410.20.
- **Interval Empirical Coverage (80% Target):** 82.4% empirical coverage.
- **Interval Empirical Coverage (95% Target):** 96.1% empirical coverage.

## 5. Drift Monitoring & Recalibration Strategy
- **Continuous Tracking:**
  - Evaluates forecast error (MAPE) as actual settlement data arrives each month.
  - Drift worker (`drift_job.py`) computes Population Stability Index (PSI) and Kolmogorov-Smirnov (KS) statistics between feature distributions.
- **Alert Thresholds:**
  - Feature PSI > 0.20: Triggers Prometheus alert `MLFeatureDriftWarning`.
  - Monthly MAPE deviation > 15%: Triggers alert `MLForecastErrorDegraded`.

## 6. Cold-Start & Graceful Degradation
- If a user has fewer than 3 months of history, the API emits status `INSUFFICIENT_DATA` (HTTP 422 with actionable guidance) or falls back to a conservative rule-based rule-of-thumb baseline (50/30/20 of stated income) with `confidence: 0.50` and an explicit assumption note.
