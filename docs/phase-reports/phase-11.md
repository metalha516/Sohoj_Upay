# Phase 11 — Pure Deterministic Financial Engine Report

## Executive Summary

Phase 11 implements the deterministic, mathematically rigorous financial calculation engine for the **Sohoj** platform under `backend/app/financial/`, adhering strictly to `design.md` §6.

The financial engine is designed with **zero dependencies** on databases, ORMs, machine learning models, or external API frameworks. All calculations use Python's `decimal.Decimal` with an explicit `ROUND_HALF_UP` quantization policy to eliminate IEEE-754 floating-point drift. Every calculation result returns a strongly typed dataclass containing an explicit `assumptions` block with mandatory `rate_type` declaration (`"assumed" | "historical" | "contractual"`), establishing full auditability and transparent AI explainability.

---

## 1. Architecture & Dependency Boundary Isolation

The package structure enforces a strict architectural boundary:

```
backend/app/financial/
├── __init__.py          # Clean public API re-exports for engine, schemas, rounding, and exceptions
├── rounding.py          # Centralized ROUND_HALF_UP rounding and quantization policies
├── exceptions.py        # Strongly typed financial domain exceptions
├── schemas.py           # Dataclass return contracts with assumptions blocks
├── engine.py            # Pure deterministic implementations of all 9 financial engines
└── calculator.py        # Backwards-compatible facade delegating to engine.py
```

### AST Import Boundary Verification
An automated AST-level verification test (`test_ast_import_boundary`) parses the abstract syntax tree of every source file in `backend/app/financial/` and verifies that no imports originate from:
- `sqlalchemy`, `fastapi`, `starlette`, `pydantic`
- `app.models`, `app.db`, `app.services`, `app.api`, `app.ml`
- `ml`, `torch`, `sklearn`, `lightgbm`, `xgboost`, `joblib`

The engine relies exclusively on Python standard library modules (`decimal`, `dataclasses`, `datetime`, `math`, `calendar`, `typing`).

---

## 2. Explicit Rounding Policy & Precision Architecture

Implemented in `backend/app/financial/rounding.py`:

| Target Metric | Decimal Precision | Quantization Rounding Mode | Target Helper |
|---|---|---|---|
| **Monetary Values (BDT ৳)** | `0.01` (2 decimal places) | `ROUND_HALF_UP` | `round_currency(val)` |
| **Rates & Percentages (%)** | `0.0001` (4 decimal places) | `ROUND_HALF_UP` | `round_rate(val)` |
| **Ratios & Indexes** | `0.000001` (6 decimal places) | `ROUND_HALF_UP` | `round_ratio(val)` |

### Internal Workspace Precision
Intermediate arithmetic within `engine.py` operates under an isolated high-precision context:
```python
with localcontext() as ctx:
    ctx.prec = 35  # 35 significant decimal digits
```
Quantization occurs strictly at the terminal step when instantiating the return dataclass.

---

## 3. Implemented Financial Calculation Engines

### 3.1 `calculate_future_value`
- **Formulas:**
  - Lump Sum: $A = P \times \left(1 + \frac{r}{n}\right)^{n \cdot t}$
  - Monthly Contributions:
    - Effective monthly compounding: $i_m = \left(1 + \frac{r}{n}\right)^{n/12} - 1$ (for $n=12$, $i_m = \frac{r}{12}$)
    - Ordinary Annuity (`timing="end"`): $\text{FV}_m = m \times \left[\frac{(1 + i_m)^M - 1}{i_m}\right]$
    - Annuity Due (`timing="begin"`): $\text{FV}_m = m \times \left[\frac{(1 + i_m)^M - 1}{i_m}\right] \times (1 + i_m)$
  - Zero-Rate Special Case ($r = 0$): $\text{FV} = P + m \times M$, $\text{Growth} = \text{৳}0.00$
- **Discrete Compounding Frequencies:** $n \in \{1, 2, 4, 12, 365\}$
- **Yearly Series:** Produces `list[YearlyPoint]` with `year`, `balance`, `contributions`, and `growth`.

### 3.2 `calculate_doubling_time`
- **Closed-Form Formula:**
  $$t = \frac{\ln(2)}{n \cdot \ln\left(1 + \frac{r}{n}\right)}$$
  Computed via `Decimal.ln()`.
- **Rule of 72 Reference:** Included in assumptions for heuristic benchmark ($t_{\text{approx}} = \frac{72}{r \times 100}$).
- **Preconditions:** $r > 0$ strictly enforced (raises `InvalidRateError` if $r \le 0$).

### 3.3 `calculate_monthly_required_saving`
- **Formula:** Solves the annuity accumulation equation for required monthly deposit $m$:
  - When $r = 0$: $m = \frac{\text{Target} - \text{Current}}{\text{Months}}$
  - When $r > 0$: $\text{Rem} = \text{Target} - \text{Current} \times (1+i)^M \implies m = \frac{\text{Rem} \times i}{(1+i)^M - 1}$
- **Target Met Edge Case:** If $\text{Current} \ge \text{Target}$ or existing funds compound to exceed target, returns $m = \text{৳}0.00$.

### 3.4 `calculate_goal_progress`
- **Parameters:** `target`, `current`, `target_date`, `today`, `avg_monthly_saving`.
- **Calendar Months Remaining:** Exactly evaluates calendar interval under `Asia/Dhaka` timeline.
- **Feasibility Categorization:**
  - `completed`: $\text{Current} \ge \text{Target}$
  - `on_track`: Projected completion date $\le$ target date based on observed velocity.
  - `at_risk`: Shortfall requires slightly more time ($+1 \dots 2$ months) than remaining.
  - `behind`: Velocity significantly lags required rate or zero saving rate recorded.

### 3.5 `calculate_savings_rate` & `calculate_expense_ratio`
- **Data Contract Conformance:** Follows `docs/data/data-contract.md` §1.2:
  $$\text{Savings Rate} = \begin{cases} \left(\frac{\text{Savings}}{\text{Income}}\right) \times 100 & \text{if } \text{Income} > 0 \\ \text{null} & \text{if } \text{Income} \le 0 \end{cases}$$
- Returns `Decimal | None`, correctly preserving `None` for zero or negative income months.

### 3.6 `calculate_emergency_fund`
- **Metrics:** Evaluates runway against essential monthly expenses:
  $$\text{Months Covered} = \frac{\text{Current Fund}}{\text{Avg Monthly Essentials}}$$
- **Categorization Tiers:**
  - `critical`: $< 1.0$ month coverage
  - `vulnerable`: $1.0 \dots < 3.0$ months coverage
  - `adequate`: $3.0 \dots < 6.0$ months coverage
  - `optimal`: $\ge 6.0$ months coverage

### 3.7 `calculate_affordability`
- **Liquidity Buffer Evaluation:**
  $$\text{Available Liquidity} = \text{Balance} - \text{Upcoming Commitments} - \text{Goals Impact}$$
  $$\text{Remaining Buffer} = \text{Available Liquidity} - \text{Purchase Amount}$$
- **Verdicts:**
  - `affordable_from_cash`: Purchase safely funded from available cash buffer today ($\text{Remaining Buffer} \ge 0$).
  - `affordable_with_monthly_budget`: Immediate deficit, but positive monthly surplus can absorb within $\le 3$ months.
  - `unaffordable_cash_deficit`: Requires $> 3$ months surplus or user runs negative cash surplus.

### 3.8 `run_scenario`
- **Comparative Modeling:** Evaluates baseline financial parameters (`initial_balance`, `monthly_income`, `monthly_expense`, `monthly_savings`, `annual_return_rate`) against hypothetical parameter overrides.
- **Output:** Returns yearly progression (`ScenarioYearPoint`) comparing baseline vs simulated balance and net monetary benefit.

---

## 4. Assumption Transparency & Audit Contracts

All projection dataclasses require an `AssumptionsBlock`:
```python
@dataclass(frozen=True)
class AssumptionsBlock:
    rate_type: Literal["assumed", "historical", "contractual"]
    annual_rate: Decimal
    compounding_per_year: int = 12
    contribution_timing: str = "end"
    inflation_adjusted: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
```
- `rate_type`: Enforces explicit labeling so the downstream GenAI safety layer never portrays an assumed projection as guaranteed or contractual.
- `disclaimer_code`: Standardized default `"PROJECTION_NOT_GUARANTEED"`.

---

## 5. Typed Exception Hierarchy

Defined in `backend/app/financial/exceptions.py`:

```
FinancialEngineError (Base)
├── NegativeValueError            (Negative amounts, balances, contributions)
├── ZeroPeriodError               (Horizon <= 0 months or years)
├── InvalidRateError              (Negative rate, rate > 1000%, NaN, Infinity)
├── InvalidCompoundingFrequencyError (Frequency not in [1, 2, 4, 12, 365])
├── InvalidTimingError            (Timing not in ['end', 'begin'])
└── InvalidTargetDateError        (Target date in past with outstanding shortfall)
```

---

## 6. Verification & Test Matrix

### Test Suite Execution Summary
- **Test File:** `backend/tests/unit/test_financial_engine.py` (and `test_financial.py`)
- **Total Tests:** 39 passed in 0.92 seconds
- **Repository Total:** 108 passed across the entire backend suite

### Coverage Report (`app.financial.*`)
```
Name                                  Stmts   Miss  Cover   Missing
-------------------------------------------------------------------
backend\app\financial\__init__.py         6      0   100%
backend\app\financial\calculator.py      17      1    94%   24
backend\app\financial\engine.py         264      4    98%   124, 456, 472, 659
backend\app\financial\exceptions.py      33      0   100%
backend\app\financial\rounding.py        11      0   100%
backend\app\financial\schemas.py        110      0   100%
-------------------------------------------------------------------
TOTAL                                   441      5    99%
```

### Property-Based Testing (Hypothesis)
1. **Monotonicity in Rate:** For fixed principal and horizon, higher return rates strictly yield equal or greater future value.
2. **Monotonicity in Time:** For positive rates and contributions, longer horizons strictly increase future value.
3. **Lower Bound Guarantee:** For all non-negative rates, future value is mathematically bounded by total contributions: $\text{FV} \ge \text{Total Contributed}$.
4. **Doubling Time Identity:** Doubling time $t$ evaluated in future value formula satisfies:
   $$P \times \left(1 + \frac{r}{n}\right)^{n \cdot t} \approx 2P \quad (\pm 2\% \text{ discrete tolerance})$$
5. **Scale Invariance:** Multiplying income and savings by scalar factor $k > 0$ yields invariant savings rates.

### Static Analysis & Quality Gates
- `mypy --strict`: **PASS** (`[mypy-app.financial.*] strict = true` enforced with zero issues across 91 files).
- `ruff check`: **PASS** (zero linter warnings).
- `ruff format`: **PASS** (100% PEP 8 compliant formatting).
- Boundary Test: **PASS** (zero illegal imports).
