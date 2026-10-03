# Phase 02 Report — Domain Definitions, Data Contract & Persona Specification

**Date:** 2026-10-03  
**Status:** Completed  
**Author:** Antigravity Autonomous Agent  

---

## 1. Executive Summary
Phase 2 delivered a mathematically rigorous, domain-specific foundation for all downstream database schemas, financial calculation engines, synthetic data generation, and machine learning models. Ambiguities identified in `design.md` §4.3 regarding savings, transfers, fees, and wallet balance dynamics have been resolved in [data-contract.md](file:///d:/DIU%20Project/docs/data/data-contract.md). All taxonomy, persona, occupation, and anomaly bounds are stored in declarative YAML configs and backed by unit-tested Pydantic v2 validation models.

---

## 2. What Was Built

### 2.1 Comprehensive Data Contract (`docs/data/data-contract.md`)
- **Metric Definitions:**
  - Standardized month boundaries to `Asia/Dhaka` timezone (UTC+6).
  - Pure mathematical formulas for Income, Expense, Savings, Unallocated Surplus, Savings Rate, and Running Balance.
  - Explicit transfer and cash-in semantics: `cash_in_self` is treated strictly as an asset conversion (not income).
  - Explicit savings semantics: Residual unspent wallet balances are designated as **Unallocated Surplus** and are *never* automatically counted as savings. Savings requires explicit allocation to a goal or DPS installment.
  - Treatment of MFS cash-out and P2P fees as necessity expenses.
- **5 Detailed Worked Numeric Examples:**
  - Salaried corporate executive (23.08% savings rate).
  - Garment worker with high agent cash-out and P2P remittance (3.03% savings rate, slight deficit against opening balance).
  - Tech freelancer with volatile milestone earnings and bank DPS deposit (25.00% savings rate).
  - University student reliant on family support and non-income wallet loads (0.00% savings rate).
  - Micro-merchant transacting high customer volume with wholesale cash-out fee leakage (0.00% savings rate).
- **Taxonomy (2 Levels):**
  - 4 high-level purposes: `necessity`, `savings_goal`, `discretionary`, `other`.
  - 25 fine-grained MFS categories covering Bangladesh everyday life (bazaar groceries, mess/apartment rent, utility pay bills, mobile recharge, education fees, microfinance installments, MFS tariffs, Eid festivals, Zakat, and DPS deposits).
- **Behavioral Persona Specifications:**
  - 6 fixed archetypes ($15.0\%$ target share each $= 90\%$) + 1 mixed/drifting persona ($10.0\%$ target share):
    1. `consistent_saver`: High savings rate (28% mean), regular monthly income, low variance.
    2. `balanced_spender`: Moderate savings (15% mean), balanced lifestyle, moderate cash-out.
    3. `tight_budgeter`: Subsistence living (3% mean savings), 88% necessity share, low wallet balance.
    4. `discretionary_spender`: High impulse/lifestyle allocation (38% discretionary), low savings (6% mean).
    5. `volatile_earner`: Irregular/lumpy milestone earnings, extreme variance, periodic savings lumps.
    6. `cash_dominant_transactor`: Rapid agent cash-out (82% volume ratio), uses MFS as conduit.
    7. `mixed_drifting`: Transitional multi-modal group experiencing seasonal shocks or drifting habits.
- **Occupation & Segment Model:**
  - 8 realistic socioeconomic segments (Garment worker, student, private employee, civil servant, freelancer, shopkeeper, ride-share driver, remittance recipient).
  - Empirical BDT income distributions (Min, P10, P25, Median, P75, P90, Max).
  - Probabilistic many-to-many transition matrix into behavioral personas.
- **Ground-Truth Schema (`synthetic_ground_truth`):**
  - Quarantined schemas for `synthetic_user_ground_truth` and `synthetic_transaction_ground_truth`.
  - Strict isolation contract guaranteeing no label leakage into feature stores.
- **Phase 5 Realism Metrics List:**
  - Statistical quality gates: $N \ge 600$, 12 months, $\ge 100\text{k}$ transactions, 2.0%–3.0% injected anomalies, round cash-out clustering ($\ge 80\%$), and $\ge 1.4\times$ Eid seasonality bumps.

### 2.2 Declarative YAML Configuration Architecture
- `data/synthetic/config/taxonomy.yaml`: 4 purposes and 25 Bangladeshi MFS categories with BDT ranges and frequencies.
- `data/synthetic/config/personas.yaml`: 7 personas with income bands, savings rates, spend mixes, and cash-out distributions.
- `data/synthetic/config/occupations.yaml`: 8 occupations with income percentiles and persona transition matrices.
- `data/synthetic/config/anomalies.yaml`: 4 anomaly types and 5 life-event shock configurations.

### 2.3 Pydantic Validation & Automated Testing
- `backend/app/schemas/synthetic_config.py`:
  - `TaxonomyConfig`, `PersonasConfig`, `OccupationsConfig`, `AnomaliesConfig`.
  - Enforces cross-field validations: non-decreasing income percentiles, positive amount bounds, spend mix shares summing to 1.00, persona transition probabilities summing to 1.00, population shares summing to 1.00, and anomaly probabilities summing to 1.00.
- `backend/tests/unit/test_synthetic_config.py`:
  - 4 automated unit tests verifying schema conformance and relational consistency between YAML configuration files.

---

## 3. Assumptions Requiring User Sign-Off

As required by Acceptance Criteria, the following empirical domain assumptions have been codified in the YAML configurations and are flagged for formal sign-off:

1. **Self Cash-In Treatment:**
   - *Assumption:* A cash-in at an MFS agent into one's own wallet is an asset conversion and is **never** counted as monthly income.
   - *Alternative:* Some informal workers receive direct payments via agent cash-in. We address this by providing `category = family_support_received` or `category = business_revenue` for external cash-ins.
2. **Savings Definition & Residual Surplus:**
   - *Assumption:* Unspent wallet balances at the end of a month are classified as **Unallocated Surplus**, not Savings. Savings requires an explicit intentional goal contribution or DPS installment.
3. **MFS Cash-Out Tariff Calibration:**
   - *Assumption:* Calibrated at ৳18.50 per ৳1,000 ($1.85\%$) for standard app withdrawals, and ৳14.90 per ৳1,000 ($1.49\%$) for designated Priyo Agent withdrawals.
4. **RMG Garment Worker Income Band:**
   - *Assumption:* Calibrated to the late 2023 Gazette baseline of ৳12,500/month basic minimum wage, extending to ৳22,000–৳28,000 with overtime and seniority allowances.
5. **Target Population Mix:**
   - *Assumption:* Exact equal partition ($15.0\%$ each) across the 6 core archetypes ($= 90\%$) with $10.0\%$ reserved for the mixed/drifting group to ensure realistic classifier overlap.

---

## 4. Verification & Test Results

### 4.1 Pytest Suite Output
```text
tests/unit/test_errors.py::test_404_returns_rfc7807_problem_details PASSED
tests/unit/test_errors.py::test_security_headers_present_on_all_responses PASSED
tests/unit/test_financial.py::test_calculate_savings_rate PASSED
tests/unit/test_financial.py::test_calculate_future_value PASSED
tests/unit/test_health.py::test_health_endpoint PASSED
tests/unit/test_health.py::test_api_v1_health_endpoint PASSED
tests/unit/test_health.py::test_ready_endpoint_handles_unreachable_services PASSED
tests/unit/test_logging.py::test_scrub_message_removes_sensitive_data PASSED
tests/unit/test_logging.py::test_json_formatter_outputs_valid_json PASSED
tests/unit/test_synthetic_config.py::test_taxonomy_yaml_validates PASSED
tests/unit/test_synthetic_config.py::test_personas_yaml_validates PASSED
tests/unit/test_synthetic_config.py::test_occupations_yaml_validates PASSED
tests/unit/test_synthetic_config.py::test_anomalies_yaml_validates PASSED

======================== 13 passed in 2.82s ========================
```

### 4.2 Ruff Linter & Formatter
```text
$ python -m ruff check .
All checks passed!

$ python -m ruff format --check .
37 files already formatted.
```

### 4.3 Mypy Static Type Checking
```text
$ python -m mypy --config-file mypy.ini backend/app
Success: no issues found in 24 source files
```

### 4.4 Secret Scanner
```text
$ python infra/ci_secret_scan.py
[PASS] Secret Scan PASSED! No secrets or credentials found.
```

---

## 5. Known Gaps & Next Phase Needs

### Known Gaps (Tracked in `docs/PROGRESS.md`)
- Phase 3 will build User Authentication, Argon2id hashing, and JWT session handling.
- Phase 4 will implement the full deterministic synthetic data generator utilizing these validated YAML parameters.

### What Phase 3 Needs
- User model schema with security baseline (Argon2id, refresh token hashes).
- Role-based authorization policies and security headers.
