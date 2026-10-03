# Model Card: Transaction Anomaly & Unusual Spending Detection (Model B)

## 1. Model Details
- **Model Name:** Sohoj Isolation Forest Anomaly Detector (`model_b_anomaly_detector`)
- **Version:** `1.0.0`
- **Model Type:** Isolation Forest (`sklearn.ensemble.IsolationForest`) with Bengali Festival Rule Guards
- **Framework:** Scikit-Learn
- **Release Date:** October 2026
- **License:** Proprietary (Sohoj Financial Coach)
- **Maintainer:** Sohoj ML Engineering Team

## 2. Intended Use & Target Task
- **Primary Use:** Autonomously flag anomalous transactions (unusually large cash-outs, rapid high-frequency burst spending, irregular merchant categories) directly after transaction settlement.
- **Alert Budget Guarantee:** At most 3 high-priority proactive alerts per user per month to eliminate notification fatigue.
- **Out of Scope:** Regulatory AML/CFT reporting or hard card-blocking decisions (the model surfaces advisory alerts with confirm/dismiss user actions).

## 3. Training Data & Features
- **Data Source:** Synthetic MFS/Bank transaction stream (32,000+ transactions across 600 users over 12 months), incorporating injected anomaly ground truth and calendar-aligned Bengali cultural festivals.
- **Feature Vector:**
  - `amount`: Raw transaction amount in BDT.
  - `amount_zscore_30d`: Standardized transaction magnitude against user's trailing 30-day mean and variance.
  - `category_rarity`: Log-frequency of the merchant category for this specific user.
  - `hour_of_day`: Normalized transaction timestamp hour.
  - `is_cashout`: Binary flag for MFS cash-out operations.
  - `festival_proximity_days`: Integer distance in days to nearest cultural festival (Eid-ul-Fitr, Eid-ul-Adha, Durga Puja, Pohela Boishakh).

## 4. Performance & Evaluation Metrics
- **Contamination Parameter:** 0.03 (targeted 3% anomaly expectation).
- **Precision:** 0.842
- **Recall:** 0.816
- **ROC-AUC:** 0.924
- **Precision-Recall AUC (PR-AUC):** 0.791
- **Alert Budget Enforcement:** 100% of synthetic test users received ≤ 3 alerts/month.

## 5. Festival Awareness & False Positive Mitigation
- **Festival Guard Logic:** In the 10 days leading up to Eid-ul-Fitr and Eid-ul-Adha, Bangladeshi household spending surges by 2.5x–4x (shopping, remittances, sacrificial animal purchases).
- The model employs an adaptive threshold adjustment factor:
  $$\text{threshold}_{\text{effective}} = \text{threshold}_{\text{base}} \times \left(1 + \frac{\alpha}{\max(1, d_{\text{festival}})}\right)$$
  This dynamic boundary reduces false-positive alert spikes during holiday seasons from 28.4% down to 3.1%.

## 6. Feedback Loop & User Agency
- Anomalies are surfaced via `GET /api/v1/anomalies` with `status: pending`.
- Users can confirm (`PATCH ... {"status": "confirmed"}`) or dismiss (`PATCH ... {"status": "dismissed"}`).
- Dismissed anomalies update user-level category baseline priors to prevent repetitive alerts for user-intentional expenses.
