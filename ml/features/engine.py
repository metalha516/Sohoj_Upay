"""Feature engineering engine computing base monthly facts and rolling window features."""

import math
import uuid
import zoneinfo
from collections import defaultdict
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import numpy as np
import pandas as pd

from ml.features.schema import FEATURE_SCHEMA_VERSION, MonthlyFeatureRecord

DHAKA_TZ = zoneinfo.ZoneInfo("Asia/Dhaka")


def to_dhaka_date(ts_input: Any) -> tuple[date, date]:
    """Parse timestamp into Asia/Dhaka local date and normalized first-of-month date.

    Returns:
        (dhaka_local_date, month_start_date)
    """
    if isinstance(ts_input, str):
        # Handle ISO strings
        dt = datetime.fromisoformat(ts_input)
    elif isinstance(ts_input, pd.Timestamp):
        dt = ts_input.to_pydatetime()
    elif isinstance(ts_input, datetime):
        dt = ts_input
    else:
        raise ValueError(f"Unsupported timestamp format: {ts_input}")

    if dt.tzinfo is None:
        # Naive datetime assumed to be UTC
        dt = dt.replace(tzinfo=UTC)

    # Convert strictly to Asia/Dhaka timezone
    dt_dhaka = dt.astimezone(DHAKA_TZ)
    local_date = dt_dhaka.date()
    month_start = date(local_date.year, local_date.month, 1)
    return local_date, month_start


class MonthlyFeatureEngine:
    """Core deterministic feature computation engine shared by training and online serving."""

    def __init__(self, schema_version: str = FEATURE_SCHEMA_VERSION) -> None:
        self.schema_version = schema_version

    def compute_user_features(
        self, user_id: uuid.UUID, transactions: list[dict[str, Any]] | pd.DataFrame
    ) -> list[MonthlyFeatureRecord]:
        """Compute complete monthly features and rolling windows for a single user."""
        if isinstance(transactions, pd.DataFrame):
            txns = transactions.to_dict(orient="records")
        else:
            txns = list(transactions)

        if not txns:
            return []

        # 1. Bucket transactions by Asia/Dhaka month
        monthly_buckets: dict[date, list[dict[str, Any]]] = defaultdict(list)
        for t in txns:
            ts_val = t.get("ts") or t.get("created_at") or t.get("timestamp")
            if ts_val is None:
                raise ValueError(f"Transaction missing timestamp ('ts' or 'created_at'): {t}")
            _, m_start = to_dhaka_date(ts_val)
            monthly_buckets[m_start].append(t)

        sorted_months = sorted(monthly_buckets.keys())
        base_features_by_month: dict[date, dict[str, Any]] = {}

        # 2. Compute base monthly aggregates for each month
        prev_month_expense: Decimal | None = None
        for m in sorted_months:
            m_txns = monthly_buckets[m]
            base_data = self._compute_base_month(user_id, m, m_txns, prev_month_expense)
            base_features_by_month[m] = base_data
            prev_month_expense = base_data["expense"]

        # 3. Compute rolling 3-month features across sorted chronological months
        records: list[MonthlyFeatureRecord] = []
        for i, m in enumerate(sorted_months):
            # Window of up to 3 consecutive months: [i-2, i-1, i]
            window_slice = [
                base_features_by_month[sorted_months[j]] for j in range(max(0, i - 2), i + 1)
            ]
            rolling_data = self._compute_rolling_3m(window_slice)

            merged_data = {**base_features_by_month[m], **rolling_data}
            merged_data["feature_schema_version"] = self.schema_version
            merged_data["computed_at"] = datetime.now(UTC)

            records.append(MonthlyFeatureRecord.model_validate(merged_data))

        return records

    def _compute_base_month(
        self,
        user_id: uuid.UUID,
        month: date,
        txns: list[dict[str, Any]],
        prev_expense: Decimal | None,
    ) -> dict[str, Any]:
        """Compute base features for a single month honoring data-contract.md §1 rules."""
        income = Decimal("0.00")
        expense = Decimal("0.00")
        savings = Decimal("0.00")
        necessity_expense = Decimal("0.00")
        discretionary_expense = Decimal("0.00")
        cashout_count = 0
        all_amounts: list[float] = []
        expense_amounts: list[float] = []
        category_breakdown: dict[str, float] = defaultdict(float)

        for t in txns:
            amt = Decimal(str(t["amount"]))
            fee = Decimal(str(t.get("fee", 0.0) or 0.0))
            txn_type = str(
                t.get("txn_type") or t.get("transaction_type") or t.get("type") or ""
            ).lower()
            category = str(t.get("category", "") or "")
            purpose = str(t.get("purpose", "") or "")

            all_amounts.append(float(amt))

            # -------------------------------------------------------------
            # Rule 1: Inflows & Income
            # cash_in_self is an asset load, NOT earned income
            # -------------------------------------------------------------
            if (
                txn_type in ("income", "transfer_in")
                or (txn_type == "cash_in" and category != "cash_in_self")
            ) and category != "cash_in_self":
                income += amt

            # -------------------------------------------------------------
            # Rule 2: Cash-Outs
            # -------------------------------------------------------------
            elif txn_type in ("cash_out", "cashout"):
                cashout_count += 1
                if purpose == "savings_goal":
                    # Cash withdrawn specifically to deposit in external savings
                    savings += amt
                    expense += fee  # Fee only is expense
                    if fee > Decimal("0.00"):
                        expense_amounts.append(float(fee))
                        category_breakdown["mfs_fee"] += float(fee)
                else:
                    # Consumption cash-out (necessity, discretionary, other)
                    tot_outflow = amt + fee
                    expense += tot_outflow
                    expense_amounts.append(float(tot_outflow))
                    category_breakdown[category] += float(amt)
                    if fee > Decimal("0.00"):
                        category_breakdown["mfs_fee"] += float(fee)

                    if purpose == "necessity":
                        necessity_expense += tot_outflow
                    elif purpose == "discretionary":
                        discretionary_expense += tot_outflow

            # -------------------------------------------------------------
            # Rule 3: Digital Expenses & MFS Fees
            # -------------------------------------------------------------
            elif txn_type in ("expense", "payment"):
                tot_outflow = amt + fee
                expense += tot_outflow
                expense_amounts.append(float(tot_outflow))
                category_breakdown[category] += float(amt)
                if fee > Decimal("0.00"):
                    category_breakdown["mfs_fee"] += float(fee)

                if purpose == "necessity":
                    necessity_expense += tot_outflow
                elif purpose == "discretionary":
                    discretionary_expense += tot_outflow

            # -------------------------------------------------------------
            # Rule 4: Transfers & Savings
            # Internal transfers are not expenses unless dedicated to savings
            # -------------------------------------------------------------
            elif txn_type in ("transfer", "transfer_out"):
                if purpose == "savings_goal":
                    savings += amt
                elif purpose in ("necessity", "discretionary") and category in (
                    "family_support",
                    "donation",
                ):
                    tot_outflow = amt + fee
                    expense += tot_outflow
                    expense_amounts.append(float(tot_outflow))
                    category_breakdown[category] += float(amt)
                    if fee > Decimal("0.00"):
                        category_breakdown["mfs_fee"] += float(fee)
                    if purpose == "necessity":
                        necessity_expense += tot_outflow
                    elif purpose == "discretionary":
                        discretionary_expense += tot_outflow
                elif fee > Decimal("0.00"):
                    # Fee on transfer if any
                    expense += fee
                    expense_amounts.append(float(fee))
                    category_breakdown["mfs_fee"] += float(fee)

        # -----------------------------------------------------------------
        # Derived Metric Calculations
        # -----------------------------------------------------------------
        # Savings Rate: null if income <= 0
        savings_rate: Decimal | None = None
        if income > Decimal("0.00"):
            savings_rate = Decimal(str(round(float(savings / income), 4)))

        # Necessity & Discretionary Rates: null if expense <= 0
        necessity_rate: Decimal | None = None
        discretionary_rate: Decimal | None = None
        income_expense_ratio: Decimal | None = None
        if expense > Decimal("0.00"):
            necessity_rate = Decimal(str(round(float(necessity_expense / expense), 4)))
            discretionary_rate = Decimal(str(round(float(discretionary_expense / expense), 4)))
            income_expense_ratio = Decimal(str(round(float(income / expense), 4)))

        # Transaction Statistics
        txn_count = len(txns)
        avg_txn: Decimal | None = None
        median_txn: Decimal | None = None
        if all_amounts:
            avg_txn = Decimal(str(round(float(np.mean(all_amounts)), 2)))
            median_txn = Decimal(str(round(float(np.median(all_amounts)), 2)))

        # Expense Variance (Sample Variance, N >= 2)
        expense_variance: Decimal | None = None
        if len(expense_amounts) >= 2:
            var_val = float(np.var(expense_amounts, ddof=1))
            expense_variance = Decimal(str(round(var_val, 4)))
        elif len(expense_amounts) == 1:
            expense_variance = Decimal("0.0000")

        # MoM Spending Growth
        spending_growth: Decimal | None = None
        if prev_expense is not None and prev_expense > Decimal("0.00"):
            growth_val = float((expense - prev_expense) / prev_expense)
            spending_growth = Decimal(str(round(growth_val, 4)))

        return {
            "user_id": user_id,
            "month": month,
            "income": income,
            "expense": expense,
            "savings": savings,
            "savings_rate": savings_rate,
            "necessity_expense": necessity_expense,
            "discretionary_expense": discretionary_expense,
            "necessity_rate": necessity_rate,
            "discretionary_rate": discretionary_rate,
            "txn_count": txn_count,
            "cashout_count": cashout_count,
            "avg_txn": avg_txn,
            "median_txn": median_txn,
            "expense_variance": expense_variance,
            "spending_growth": spending_growth,
            "income_expense_ratio": income_expense_ratio,
            "category_breakdown": dict(category_breakdown),
        }

    def _compute_rolling_3m(self, window_slice: list[dict[str, Any]]) -> dict[str, Any]:
        """Compute rolling 3-month metrics over a slice of up to 3 consecutive months."""
        # Savings rates
        valid_srs = [
            float(b["savings_rate"]) for b in window_slice if b["savings_rate"] is not None
        ]
        rolling_sr_mean = float(np.mean(valid_srs)) if valid_srs else None
        rolling_sr_std = (
            float(np.std(valid_srs, ddof=1)) if len(valid_srs) >= 2 else 0.0 if valid_srs else None
        )

        savings_consistency: Decimal | None = None
        if rolling_sr_std is not None:
            savings_consistency = Decimal(str(round(rolling_sr_std, 4)))

        # Expenses
        expenses = [float(b["expense"]) for b in window_slice]
        rolling_exp_mean = float(np.mean(expenses)) if expenses else None
        rolling_exp_std = (
            float(np.std(expenses, ddof=1)) if len(expenses) >= 2 else 0.0 if expenses else None
        )

        # Spending Trend: slope of expenses over the window
        spending_trend: float | None = None
        if len(expenses) >= 2:
            x = np.arange(len(expenses))
            # Linear slope
            slope, _ = np.polyfit(x, expenses, 1)
            spending_trend = round(float(slope), 2)
        elif len(expenses) == 1:
            spending_trend = 0.0

        # Category Entropy: Shannon entropy across aggregated category spend
        cat_totals: dict[str, float] = defaultdict(float)
        for b in window_slice:
            for cat, amt in b.get("category_breakdown", {}).items():
                cat_totals[cat] += amt

        tot_spend = sum(cat_totals.values())
        entropy: float = 0.0
        if tot_spend > 0:
            for amt in cat_totals.values():
                if amt > 0:
                    p = amt / tot_spend
                    entropy -= p * math.log(p)
        category_entropy = round(float(entropy), 4)

        # Discretionary Volatility
        valid_discs = [
            float(b["discretionary_rate"])
            for b in window_slice
            if b["discretionary_rate"] is not None
        ]
        disc_vol = (
            float(np.std(valid_discs, ddof=1))
            if len(valid_discs) >= 2
            else 0.0
            if valid_discs
            else None
        )

        # Deficit months count: Unallocated surplus = Income - Expense - Savings < 0
        deficit_count = 0
        for b in window_slice:
            surplus = b["income"] - b["expense"] - b["savings"]
            if surplus < Decimal("0.00"):
                deficit_count += 1

        return {
            "rolling_savings_rate_3m_mean": round(rolling_sr_mean, 4)
            if rolling_sr_mean is not None
            else None,
            "rolling_savings_rate_3m_std": round(rolling_sr_std, 4)
            if rolling_sr_std is not None
            else None,
            "savings_consistency": savings_consistency,
            "rolling_expense_3m_mean": round(rolling_exp_mean, 2)
            if rolling_exp_mean is not None
            else None,
            "rolling_expense_3m_std": round(rolling_exp_std, 2)
            if rolling_exp_std is not None
            else None,
            "spending_trend_3m": spending_trend,
            "category_entropy_3m": category_entropy,
            "discretionary_volatility_3m": round(disc_vol, 4) if disc_vol is not None else None,
            "deficit_months_3m": deficit_count,
        }

    def recompute_user_month_features(
        self,
        user_id: uuid.UUID,
        affected_month: date | str | None = None,
        all_user_txns: list[dict[str, Any]] | pd.DataFrame | None = None,
        target_month: date | str | None = None,
        all_user_transactions: list[dict[str, Any]] | pd.DataFrame | None = None,
    ) -> Any:
        """Incremental recompute for an affected (user, month).

        - If target_month is provided, returns the single MonthlyFeatureRecord for that month.
        - If affected_month is provided, returns all MonthlyFeatureRecord instances from that month onward.
        """
        txns = all_user_txns if all_user_txns is not None else all_user_transactions
        if txns is None:
            raise ValueError("Transactions must be provided")

        all_features = self.compute_user_features(user_id, txns)

        if target_month is not None:
            m_str = (
                target_month if isinstance(target_month, str) else target_month.strftime("%Y-%m")
            )
            for f in all_features:
                if f.month.strftime("%Y-%m") == m_str:
                    return f
            raise ValueError(f"Month {m_str} not found in computed features")

        if affected_month is not None:
            m_str = (
                affected_month
                if isinstance(affected_month, str)
                else affected_month.strftime("%Y-%m")
            )
            return [f for f in all_features if f.month.strftime("%Y-%m") >= m_str]

        return all_features
