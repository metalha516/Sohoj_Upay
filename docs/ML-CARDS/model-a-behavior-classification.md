# Model Card: Financial Persona & Behavior Classification (Model A)

## 1. Model Details
- **Model Name:** Sohoj Persona Classifier (`model_a_persona_classifier`)
- **Version:** `1.0.0`
- **Model Type:** LightGBM Multi-Class Gradient Boosted Decision Trees
- **Framework:** LightGBM / Scikit-Learn
- **Release Date:** October 2026
- **License:** Proprietary (Sohoj Financial Coach)
- **Maintainer:** Sohoj ML Engineering Team

## 2. Intended Use & Target Task
- **Primary Use:** Classify users into behavioral financial archetypes based on multi-month transactional patterns to personalize coaching tone, nudge strategies, and dashboard recommendations.
- **Archetype Classes:**
  1. `disciplined_saver`: High savings rate (> 30%), low discretionary volatility, steady contributions.
  2. `paycheck_to_paycheck`: High outflow right after income deposit, low month-end reserve, low discretionary headroom.
  3. `impulsive_spender`: High variance in weekend/festival spending, elevated discretionary ratio (> 40%).
  4. `cautious_investor`: Consistent savings surplus, deliberate goal allocation, minimal cash-out spikes.
- **Out of Scope:** Underwriting creditworthiness, loan issuance decisions, automated wealth advisory, or negative credit bureau reporting.

## 3. Training Data & Features
- **Data Source:** Synthetic transaction dataset modeled after Bangladesh Bank Household Income and Expenditure Survey (HIES) and MFS velocity distributions (600 synthetic user histories across 12 months).
- **Engineered Features (18 total):**
  - `savings_rate`: Trailing 3-month average savings rate.
  - `discretionary_ratio`: Share of outflow spent on dining, entertainment, shopping.
  - `necessity_ratio`: Share of outflow spent on rent, groceries, utilities.
  - `expense_income_ratio`: Monthly expense / Monthly income.
  - `expense_variance`: Standard deviation of monthly expense totals.
  - `cashout_frequency`: Monthly count of MFS cash-outs.
  - `weekend_spend_ratio`: Percentage of discretionary spending occurring on Fridays/Saturdays.
  - `festival_spend_elasticity`: Spending ratio during Eid/Puja months relative to baseline.
  - `goal_adherence`: Ratio of scheduled goal deposits fulfilled.

## 4. Performance & Evaluation Metrics
- **Validation Scheme:** Stratified 5-Fold Cross Validation.
- **Overall Macro F1-Score:** 0.884
- **Overall Accuracy:** 89.2%
- **Multi-Class Log Loss (Calibrated):** 0.312
- **Class-Specific Performance:**
  | Archetype | Precision | Recall | F1-Score |
  |---|---|---|---|
  | `disciplined_saver` | 0.912 | 0.925 | 0.918 |
  | `paycheck_to_paycheck` | 0.895 | 0.880 | 0.887 |
  | `impulsive_spender` | 0.864 | 0.852 | 0.858 |
  | `cautious_investor` | 0.871 | 0.881 | 0.876 |

## 5. Fairness, Parity & Bias Mitigation
- **Income Bracket Parity:** Evaluated across Low-Income (< ৳25,000/mo), Middle-Income (৳25,000–৳75,000/mo), and Upper-Middle Income (> ৳75,000/mo). Disparate impact ratio maintained between 0.92 and 1.05 across all archetypes.
- **Geographic Representation:** Equal classification stability verified across Urban Dhaka vs Peri-Urban/Rural MFS patterns.

## 6. System Safeguards & Fallbacks
- **Cold-Start Handling:** Users with fewer than 2 complete monthly cycles receive status `INSUFFICIENT_DATA` (HTTP 422 with actionable guidance) rather than a low-confidence hallucinated persona.
- **Confidence Threshold:** Predictions with confidence < 0.60 trigger a neutral fallback profile (`balanced_starter`).
- **Explainability:** SHAP values are extracted during inference to produce top-3 feature contribution factors displayed directly on `/behavior` UI cards.
