# Model A Report: Financial Behavior Archetype Classification

## 1. Executive Summary

**Model A (Behavior Classifier)** is the core behavioral profiling engine for the **Sohoj AI Financial Coach** platform. It ingests 3-month rolling financial behavior indicators and categorizes MFS accounts into one of six distinct socioeconomic archetypes (or tags them as `insufficient_data` during cold start).

To prevent user-level temporal data leakage, all cross-validation was conducted using **5-Fold Stratified Group Split (`StratifiedGroupKFold`) grouped by `user_id`**, ensuring that multiple monthly observations from the same user never span both train and evaluation folds.

### Key Benchmark Highlights
- **Beats Rule Baseline by +138%:** Macro-F1 improves from **0.3001** (rule-based baseline) to **0.7148** on the quarantined held-out seed cohort ($N=200$ users, $2,256$ evaluated months).
- **Not Suspiciously Overfit ($< 0.99$):** Held-Out Macro-F1 is **0.7148** and Accuracy is **74.47%**, reflecting realistic real-world behavioral variance without target leakage.
- **Strong Class Separability:** Macro One-vs-Rest ROC-AUC reaches **0.9427**.
- **Well-Calibrated Confidence:** Output probabilities calibrated via `CalibratedClassifierCV` achieve an Expected Calibration Error (ECE) of **0.0867** ($< 0.10$).
- **Scale Invariance (100.0%):** Proportional currency scaling ($2.0\times$) preserves identical archetype labels and confidence.
- **Cryptographic Security:** Serialized model artifacts are signed and verified against SHA-256 digests prior to deserialization.

---

## 2. Model Ladder & Cross-Validation Benchmarks

We benchmarked 5 candidate models across 5 cross-validation folds using user-stratified groupings:

| Model Architecture | 5-Fold Macro-F1 (Mean ± Std) | 5-Fold Accuracy (Mean ± Std) | Key Characteristics & Trade-offs |
|---|---|---|---|
| **Rule-Based Baseline** | $0.3001 \pm 0.0188$ | $0.3930 \pm 0.0131$ | Hard thresholds; poor recall on edge cases and volatile earners. |
| **Logistic Regression (L2)** | $0.6071 \pm 0.0240$ | $0.6427 \pm 0.0191$ | Linear decision boundaries with StandardScaler and median imputation. |
| **Random Forest (100 Trees)** | $0.6647 \pm 0.0369$ | $0.7094 \pm 0.0292$ | Non-linear ensemble; captures interaction between liquidity and savings. |
| **HistGradientBoosting (LightGBM arch.)** | $0.6928 \pm 0.0241$ | $0.7289 \pm 0.0196$ | Best discrimination, rapid histogram binning, native missing value handling. |
| **Calibrated Gradient Boosting** (Selected) | **$0.6894 \pm 0.0198$** | **$0.7272 \pm 0.0166$** | Calibrated probabilities via sigmoid scaling; reliable confidence scores. |

---

## 3. Evaluation on Held-Out Quarantined Seed Cohort

The final model was evaluated on the held-out seed cohort ($N=200$ users, seed `1337`, $2,256$ active monthly observations), which remained completely untouched throughout model exploration and training.

### 3.1 Aggregate Performance
- **Accuracy:** **74.47%**
- **Macro-F1 Score:** **0.7148**
- **Weighted-F1 Score:** **0.7478**
- **Macro ROC-AUC (One-vs-Rest):** **0.9427**
- **Expected Calibration Error (ECE):** **0.0867**

### 3.2 Per-Class Classification Report
| Archetype Class | Precision | Recall | F1-Score | Support | Description & Primary Drivers |
|---|---|---|---|---|---|
| `consistent_saver` | 0.82 | 0.81 | **0.81** | 324 | High savings rate ($\ge 20\%$), surplus buffer, disciplined DPS. |
| `tight_budgeter` | 0.76 | 0.79 | **0.77** | 444 | High necessity rate ($\ge 80\%$), low savings rate, tight balance. |
| `cash_dominant_transactor`| 0.85 | 0.88 | **0.86** | 684 | High cashout frequency ($\ge 50\%$), heavy reliance on MFS agents. |
| `discretionary_spender` | 0.64 | 0.61 | **0.62** | 204 | Elevated dining, shopping, and entertainment share ($\ge 25\%$). |
| `volatile_earner` | 0.69 | 0.67 | **0.68** | 276 | High coefficient of variation, irregular lumpy milestone earnings. |
| `balanced_spender` | 0.53 | 0.54 | **0.53** | 324 | Intermediate buffer between necessity and moderate savings. |

---

## 4. Diagnostic Visualizations

The evaluation generated high-resolution diagnostic plots in `docs/ml/figures/model_a/`:

1. **Confusion Matrix (`confusion_matrix.png`):** Demonstrates strong diagonal mass. Misclassifications occur primarily between adjacent behavioral neighbors (e.g., `balanced_spender` vs `consistent_saver`), with zero pathological confusion between polar opposites (e.g., `tight_budgeter` vs `discretionary_spender`).
2. **Reliability Diagram (`calibration_curve.png`):** The probability calibration curve closely tracks the diagonal $y = x$ reference line across all 10 confidence bins, verifying that a reported confidence of $0.80$ corresponds to an empirical accuracy of $\approx 80\%$.
3. **ROC-AUC Curves (`roc_auc_curve.png`):** Each individual archetype exhibits an AUC between **0.91** and **0.97**, establishing exceptional discriminative power.
4. **Feature Importance (`feature_importance.png`):** Permutation importance ranking matches economic intuition:
   - `cashout_frequency` (0.4032)
   - `rolling_sr_mean` (0.2210)
   - `discretionary_rate` (0.2156)
   - `income_expense_ratio` (0.1596)
   - `expense_cv` (0.1274)
   - `category_entropy` (0.1252)

---

## 5. Explainability & Human-Readable Top Factors

For every classification, the model extracts the top 3 contributing factors and formats them into **non-judgmental, purely descriptive language**:

```json
{
  "profile": "consistent_saver",
  "confidence": 0.8742,
  "top_factors": [
    {
      "feature": "rolling_sr_mean",
      "value": 0.28,
      "direction": "high",
      "label": "Savings rate: high (28.0%)"
    },
    {
      "feature": "necessity_rate",
      "value": 0.58,
      "direction": "moderate",
      "label": "Necessity expense share: moderate (58.0%)"
    },
    {
      "feature": "income_expense_ratio",
      "value": 1.42,
      "direction": "surplus",
      "label": "Income-to-expense buffer: healthy (1.42x)"
    }
  ]
}
```

### Tone Policy Enforced
- **Allowed:** "Savings rate: high", "Cash-out frequency: elevated", "Necessity expense share: concentrated in living costs".
- **Forbidden:** Moralizing or patronizing words ("good", "bad", "poor", "lazy", "foolish", "ideal").

---

## 6. Robustness & Invariance Audit

The automated robustness test suite (`python -m ml.evaluation.test_robustness`) executed 4 verification checks:

| Check | Test Method | Result | Status |
|---|---|---|---|
| **Scale Invariance** | Scaled all absolute monetary values by $2.0\times$ across 500 records | **100.00%** consistency | **PASS** |
| **Noise Perturbation** | Injected $\pm 5\%$ Gaussian noise into rates | **92.00%** label agreement | **PASS** |
| **Cold-Start Policy** | Evaluated inputs with `months_active` $\in \{0, 1\}$ | Emits `insufficient_data` ($0.0$ conf) | **PASS** |
| **Drifting Resilience** | Evaluated 564 monthly records from drifting users | 564/564 processed cleanly, mean conf $0.52$ | **PASS** |

---

## 7. Cryptographic Serialization & Security

To prevent deserialization vulnerabilities and untrusted code execution:
1. Model binary saved as `ml/artifacts/behavior_classifier_v1.joblib` with gzip compression.
2. Metadata stored in `ml/artifacts/behavior_classifier_v1_metadata.json` containing:
   - `model_version`: `"v1.0.0"`
   - `feature_schema_version`: `"v1.0.0"`
   - `dataset_hash`: `5aa9f776fef4a7a1aff95b2a40aa2cf7b8d57bfa390bf9e0e0a52e1ed0cf9a55`
   - `git_sha`: `992eb48bc96c7cd94aa1c1f8a7f8788d661ae902`
   - `sha256_checksum`: `8fbbf51ea1a975278f5ac1b4f8d711e260b7675a8ae4e470e142fe7f6d220352`
3. **Tamper Detection:** `BehaviorClassifier.load()` computes the SHA-256 digest of the artifact on disk and compares it to the metadata manifest. If any byte is altered, a `SecurityError` is raised immediately before `joblib.load()` is invoked.

---

## 8. Limitations & Operating Envelope

1. **Short History Cold Start:** Users with $< 2$ months of transactions are explicitly quarantined with `insufficient_data` and routed to rule-based onboarding guidance.
2. **Seasonal Drift:** Users undergoing Eid/festival seasonal spikes may temporarily shift from `consistent_saver` to `balanced_spender` during festival months (Ramadan/Eid). Downstream coaching logic must account for calendar month seasonality when formulating advice.
3. **Inference Latency:** Vectorized batch inference processes $> 3,000$ user-months per second ($< 0.35$ ms / record), meeting production online serving SLAs.
