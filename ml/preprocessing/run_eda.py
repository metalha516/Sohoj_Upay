"""Exploratory Data Analysis (EDA) engine and statistical evidence generation for Sohoj."""

from pathlib import Path
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

# Headless matplotlib
matplotlib.use("Agg")
plt.style.use(
    "seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default"
)


class EDAAnalyzer:
    """Performs deep statistical EDA on synthetic transaction and user cohorts."""

    def __init__(self, data_dir: Path, figures_dir: Path) -> None:
        self.data_dir = data_dir
        self.figures_dir = figures_dir
        self.figures_dir.mkdir(parents=True, exist_ok=True)

        # Load datasets
        self.df_users = pd.read_parquet(data_dir / "users.parquet")
        self.df_user_gt = pd.read_parquet(data_dir / "synthetic_user_ground_truth.parquet")
        self.df_txns = pd.read_parquet(data_dir / "transactions.parquet")
        self.df_goals = pd.read_parquet(data_dir / "financial_goals.parquet")
        self.df_contribs = pd.read_parquet(data_dir / "goal_contributions.parquet")
        self.df_txn_gt = pd.read_parquet(data_dir / "synthetic_transaction_ground_truth.parquet")

        # Prepare temporal columns
        self.df_txns["ts_dt"] = pd.to_datetime(self.df_txns["ts"])
        self.df_txns["month"] = self.df_txns["ts_dt"].dt.month
        self.df_txns["day_of_month"] = self.df_txns["ts_dt"].dt.day
        self.df_txns["hour"] = self.df_txns["ts_dt"].dt.hour
        self.df_txns["day_of_week"] = self.df_txns["ts_dt"].dt.day_name()

        # Merge user ground truth for analysis
        self.user_meta = self.df_user_gt.set_index("user_id").to_dict(orient="index")

    def compute_monthly_aggregations(self) -> pd.DataFrame:
        """Compute monthly summary features per user."""
        # Inflows (income, cash_in)
        inflow_df = (
            self.df_txns[self.df_txns["txn_type"].isin(["income", "cash_in"])]
            .groupby(["user_id", "month"])["amount"]
            .sum()
            .reset_index(name="monthly_inflow")
        )
        # Outflows (expense, cash_out)
        outflow_df = (
            self.df_txns[self.df_txns["txn_type"].isin(["expense", "cash_out"])]
            .groupby(["user_id", "month"])["amount"]
            .sum()
            .reset_index(name="monthly_outflow")
        )
        # Necessity expenses
        nec_df = (
            self.df_txns[
                (self.df_txns["txn_type"] == "expense") & (self.df_txns["purpose"] == "necessity")
            ]
            .groupby(["user_id", "month"])["amount"]
            .sum()
            .reset_index(name="necessity_spend")
        )
        # Discretionary expenses
        disc_df = (
            self.df_txns[
                (self.df_txns["txn_type"] == "expense")
                & (self.df_txns["purpose"] == "discretionary")
            ]
            .groupby(["user_id", "month"])["amount"]
            .sum()
            .reset_index(name="discretionary_spend")
        )
        # Cash-outs
        co_df = (
            self.df_txns[self.df_txns["txn_type"] == "cash_out"]
            .groupby(["user_id", "month"])
            .agg(cashout_amount=("amount", "sum"), cashout_count=("amount", "count"))
            .reset_index()
        )
        # Txn count & average
        tx_stats = (
            self.df_txns.groupby(["user_id", "month"])
            .agg(txn_count=("amount", "count"), avg_txn_amount=("amount", "mean"))
            .reset_index()
        )

        # Merge into single panel
        m = pd.merge(inflow_df, outflow_df, on=["user_id", "month"], how="outer").fillna(0.0)
        m = pd.merge(m, nec_df, on=["user_id", "month"], how="left").fillna(0.0)
        m = pd.merge(m, disc_df, on=["user_id", "month"], how="left").fillna(0.0)
        m = pd.merge(m, co_df, on=["user_id", "month"], how="left").fillna(0.0)
        m = pd.merge(m, tx_stats, on=["user_id", "month"], how="left").fillna(0.0)

        # Derived metrics
        m["savings"] = m["monthly_inflow"] - m["monthly_outflow"]
        m["savings_rate"] = np.where(
            m["monthly_inflow"] > 0,
            (m["savings"] / m["monthly_inflow"]).clip(-1.0, 1.0),
            0.0,
        )
        tot_exp = m["necessity_spend"] + m["discretionary_spend"]
        m["necessity_share"] = np.where(tot_exp > 0, m["necessity_spend"] / tot_exp, 1.0)
        m["discretionary_share"] = np.where(tot_exp > 0, m["discretionary_spend"] / tot_exp, 0.0)
        m["cashout_ratio"] = np.where(
            m["monthly_inflow"] > 0,
            (m["cashout_amount"] / m["monthly_inflow"]).clip(0.0, 1.5),
            0.0,
        )

        # Attach ground truth
        m["true_persona"] = m["user_id"].map(
            lambda u: self.user_meta[u]["true_persona"] if u in self.user_meta else "unknown"
        )
        m["true_occupation"] = m["user_id"].map(
            lambda u: self.user_meta[u]["true_occupation"] if u in self.user_meta else "unknown"
        )
        m["baseline_income"] = m["user_id"].map(
            lambda u: self.user_meta[u]["baseline_income"] if u in self.user_meta else 0.0
        )
        m["is_drifting"] = m["user_id"].map(
            lambda u: self.user_meta[u]["is_drifting"] if u in self.user_meta else False
        )

        return m

    def generate_figures_and_findings(self) -> dict[str, Any]:
        """Compute all 10 evidence findings and plot high-resolution charts."""
        monthly_df = self.compute_monthly_aggregations()
        findings: dict[str, Any] = {}

        # ---------------------------------------------------------------------
        # 1. Persona Behavior Analysis
        # ---------------------------------------------------------------------
        persona_summary = (
            monthly_df.groupby("true_persona")
            .agg(
                mean_savings_rate=("savings_rate", "mean"),
                median_savings_rate=("savings_rate", "median"),
                mean_cashout_ratio=("cashout_ratio", "mean"),
                mean_cashout_count=("cashout_count", "mean"),
                mean_discretionary_share=("discretionary_share", "mean"),
                mean_necessity_share=("necessity_share", "mean"),
            )
            .reset_index()
        )
        findings["persona_summary"] = persona_summary.to_dict(orient="records")

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        sns.barplot(
            data=persona_summary, x="true_persona", y="mean_savings_rate", palette="viridis", ax=ax1
        )
        ax1.set_title("Mean Savings Rate by Behavioral Persona", fontsize=12, fontweight="bold")
        ax1.set_xticklabels(ax1.get_xticklabels(), rotation=35, ha="right")
        ax1.set_ylabel("Savings Rate")

        sns.barplot(
            data=persona_summary, x="true_persona", y="mean_cashout_ratio", palette="magma", ax=ax2
        )
        ax2.set_title("Mean Cash-Out Volume Ratio by Persona", fontsize=12, fontweight="bold")
        ax2.set_xticklabels(ax2.get_xticklabels(), rotation=35, ha="right")
        ax2.set_ylabel("Cash-Out Amount / Inflow")
        plt.tight_layout()
        fig.savefig(self.figures_dir / "eda_01_persona_profiles.png", dpi=200)
        plt.close(fig)

        # ---------------------------------------------------------------------
        # 2. Spending Composition Across Income Deciles (Engel's Law)
        # ---------------------------------------------------------------------
        user_annual = (
            monthly_df.groupby("user_id")
            .agg(
                baseline_income=("baseline_income", "first"),
                total_inflow=("monthly_inflow", "sum"),
                total_outflow=("monthly_outflow", "sum"),
                total_nec=("necessity_spend", "sum"),
                total_disc=("discretionary_spend", "sum"),
                total_cashout=("cashout_amount", "sum"),
            )
            .reset_index()
        )
        user_annual["income_decile"] = pd.qcut(
            user_annual["baseline_income"],
            q=5,
            labels=["Q1 (Lowest)", "Q2", "Q3", "Q4", "Q5 (Highest)"],
        )
        decile_spend = user_annual.groupby("income_decile", observed=False)[
            ["total_nec", "total_disc", "total_cashout"]
        ].mean()
        decile_pct = decile_spend.div(decile_spend.sum(axis=1), axis=0) * 100.0

        fig, ax = plt.subplots(figsize=(10, 5))
        decile_pct.plot(kind="bar", stacked=True, colormap="tab10", ax=ax)
        ax.set_title(
            "Annual Expenditure Mix by Income Quintile (Engel's Law)",
            fontsize=13,
            fontweight="bold",
        )
        ax.set_ylabel("Share of Total Outflow (%)")
        ax.set_xlabel("Income Quintile")
        ax.legend(
            ["Necessity Spending", "Discretionary Spending", "Cash-Out Volume"], loc="upper right"
        )
        plt.xticks(rotation=0)
        plt.tight_layout()
        fig.savefig(self.figures_dir / "eda_02_spending_composition.png", dpi=200)
        plt.close(fig)

        # ---------------------------------------------------------------------
        # 3. Volatility by Occupation (Gig workers vs Formal employees)
        # ---------------------------------------------------------------------
        user_vol = (
            monthly_df.groupby("user_id")
            .agg(
                occupation=("true_occupation", "first"),
                income_std=("monthly_inflow", "std"),
                income_mean=("monthly_inflow", "mean"),
                expense_std=("monthly_outflow", "std"),
                expense_mean=("monthly_outflow", "mean"),
            )
            .reset_index()
        )
        user_vol["income_cv"] = (
            user_vol["income_std"] / np.maximum(100.0, user_vol["income_mean"])
        ).clip(0.0, 2.0)
        user_vol["expense_cv"] = (
            user_vol["expense_std"] / np.maximum(100.0, user_vol["expense_mean"])
        ).clip(0.0, 2.0)

        fig, ax = plt.subplots(figsize=(11, 5))
        order = (
            user_vol.groupby("occupation")["income_cv"].median().sort_values(ascending=False).index
        )
        sns.boxplot(
            data=user_vol, x="occupation", y="income_cv", order=order, palette="Set3", ax=ax
        )
        ax.set_title(
            "Income Volatility (Coefficient of Variation) Across Occupations",
            fontsize=13,
            fontweight="bold",
        )
        ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha="right")
        ax.set_ylabel("Income CV (Std Dev / Mean)")
        plt.tight_layout()
        fig.savefig(self.figures_dir / "eda_03_income_expense_volatility.png", dpi=200)
        plt.close(fig)

        # ---------------------------------------------------------------------
        # 4. Monthly Seasonality (Dual Eid Spikes)
        # ---------------------------------------------------------------------
        monthly_trends = (
            self.df_txns.groupby(["month", "txn_type"])["amount"]
            .sum()
            .unstack(fill_value=0.0)
            .reset_index()
        )
        fig, ax = plt.subplots(figsize=(11, 5))
        months = [
            "Jan",
            "Feb",
            "Mar\n(Eid-Fitr)",
            "Apr\n(Boishakh)",
            "May\n(Eid-Adha)",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]
        ax.plot(
            monthly_trends["month"],
            monthly_trends["expense"] / 1e6,
            marker="o",
            linewidth=2.5,
            color="#ef4444",
            label="Expense (M BDT)",
        )
        ax.plot(
            monthly_trends["month"],
            monthly_trends["cash_out"] / 1e6,
            marker="s",
            linewidth=2.5,
            color="#f59e0b",
            label="Cash-Out (M BDT)",
        )
        ax.plot(
            monthly_trends["month"],
            monthly_trends["income"] / 1e6,
            marker="^",
            linewidth=2.5,
            color="#10b981",
            label="Income (M BDT)",
        )
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels(months)
        ax.set_title(
            "Monthly Total Transaction Volume Trends (2026 Bangladesh Calendar)",
            fontsize=13,
            fontweight="bold",
        )
        ax.set_ylabel("Total Volume (Million BDT)")
        ax.legend()
        plt.tight_layout()
        fig.savefig(self.figures_dir / "eda_04_monthly_seasonality_dual_eid.png", dpi=200)
        plt.close(fig)

        # ---------------------------------------------------------------------
        # 5. Anomaly Taxonomy & Injected Outliers
        # ---------------------------------------------------------------------
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
        anomaly_counts = self.df_txn_gt["anomaly_type"].value_counts()
        sns.barplot(x=anomaly_counts.values, y=anomaly_counts.index, palette="mako", ax=ax1)
        ax1.set_title("Injected Anomaly Counts by Type", fontsize=12, fontweight="bold")
        ax1.set_xlabel("Count")

        sns.histplot(self.df_txn_gt["severity_score"], bins=20, kde=True, color="#8b5cf6", ax=ax2)
        ax2.set_title(
            "Ground-Truth Anomaly Severity Score Distribution", fontsize=12, fontweight="bold"
        )
        ax2.set_xlabel("Severity Score (0.0 - 1.0)")
        plt.tight_layout()
        fig.savefig(self.figures_dir / "eda_05_anomaly_distributions.png", dpi=200)
        plt.close(fig)

        # ---------------------------------------------------------------------
        # 6. Cold-Start Analysis & Sparsity
        # ---------------------------------------------------------------------
        # Category frequency per user
        user_cat_counts = (
            self.df_txns[self.df_txns["txn_type"] == "expense"]
            .groupby(["user_id", "category"])
            .size()
            .reset_index(name="txn_count")
        )
        under_10_share = (user_cat_counts["txn_count"] < 10).mean() * 100.0
        findings["cold_start_under_10_cat_pct"] = float(under_10_share)

        fig, ax = plt.subplots(figsize=(9, 5))
        sns.ecdfplot(data=user_cat_counts, x="txn_count", color="#0284c7", ax=ax)
        ax.axvline(
            10,
            color="red",
            linestyle="--",
            label=f"10-txn MAD Peer Fallback Threshold ({under_10_share:.1f}% under)",
        )
        ax.set_title(
            "Empirical CDF: Transaction Frequency per (User, Category) Pair",
            fontsize=13,
            fontweight="bold",
        )
        ax.set_xlabel("Transaction Count per Year")
        ax.set_ylabel("Cumulative Probability")
        ax.set_xlim(0, 100)
        ax.legend()
        plt.tight_layout()
        fig.savefig(self.figures_dir / "eda_06_cold_start_sparsity.png", dpi=200)
        plt.close(fig)

        # ---------------------------------------------------------------------
        # 7. Correlation Heatmap Among Candidate Features
        # ---------------------------------------------------------------------
        feature_panel = monthly_df[
            [
                "savings_rate",
                "necessity_share",
                "discretionary_share",
                "cashout_ratio",
                "cashout_count",
                "txn_count",
                "avg_txn_amount",
                "monthly_inflow",
                "monthly_outflow",
            ]
        ].copy()
        corr_matrix = feature_panel.corr()

        fig, ax = plt.subplots(figsize=(9, 8))
        sns.heatmap(
            corr_matrix,
            annot=True,
            fmt=".2f",
            cmap="coolwarm",
            vmin=-1.0,
            vmax=1.0,
            cbar=True,
            ax=ax,
        )
        ax.set_title(
            "Candidate Feature Correlation Matrix (Monthly User Aggregates)",
            fontsize=13,
            fontweight="bold",
        )
        plt.tight_layout()
        fig.savefig(self.figures_dir / "eda_07_correlation_heatmap.png", dpi=200)
        plt.close(fig)

        # ---------------------------------------------------------------------
        # 8. Feature Distributions & Skewness
        # ---------------------------------------------------------------------
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        sns.histplot(
            monthly_df["monthly_outflow"], bins=30, kde=True, color="#3b82f6", ax=axes[0, 0]
        )
        axes[0, 0].set_title(
            f"Monthly Outflow (Skew: {stats.skew(monthly_df['monthly_outflow']):.2f})",
            fontweight="bold",
        )

        sns.histplot(
            np.log1p(monthly_df["monthly_outflow"]),
            bins=30,
            kde=True,
            color="#10b981",
            ax=axes[0, 1],
        )
        axes[0, 1].set_title(
            f"Log1p(Monthly Outflow) (Skew: {stats.skew(np.log1p(monthly_df['monthly_outflow'])):.2f})",
            fontweight="bold",
        )

        sns.histplot(monthly_df["savings_rate"], bins=30, kde=True, color="#f59e0b", ax=axes[1, 0])
        axes[1, 0].set_title(
            f"Savings Rate (Skew: {stats.skew(monthly_df['savings_rate']):.2f})", fontweight="bold"
        )

        sns.histplot(monthly_df["cashout_ratio"], bins=30, kde=True, color="#8b5cf6", ax=axes[1, 1])
        axes[1, 1].set_title(
            f"Cash-Out Ratio (Skew: {stats.skew(monthly_df['cashout_ratio']):.2f})",
            fontweight="bold",
        )
        plt.tight_layout()
        fig.savefig(self.figures_dir / "eda_08_feature_distributions.png", dpi=200)
        plt.close(fig)

        # Collect summary statistics for findings
        findings["total_users"] = len(self.df_users)
        findings["total_txns"] = len(self.df_txns)
        findings["total_anomalies"] = len(self.df_txn_gt)
        findings["anomaly_rate"] = len(self.df_txn_gt) / len(self.df_txns)
        findings["pearson_engels"] = float(
            stats.pearsonr(
                user_annual["baseline_income"],
                user_annual["total_nec"] / (user_annual["total_nec"] + user_annual["total_disc"]),
            )[0]
        )
        findings["freelancer_cv"] = float(
            user_vol[user_vol["occupation"] == "freelancer_gig_worker"]["income_cv"].median()
        )
        findings["govt_cv"] = float(
            user_vol[user_vol["occupation"] == "government_employee"]["income_cv"].median()
        )
        findings["mar_may_spikes"] = {
            "mar_expense_ratio": float(
                monthly_trends.loc[monthly_trends["month"] == 3, "expense"].values[0]
                / monthly_trends["expense"].mean()
            ),
            "may_outflow_ratio": float(
                (
                    monthly_trends.loc[monthly_trends["month"] == 5, "expense"].values[0]
                    + monthly_trends.loc[monthly_trends["month"] == 5, "cash_out"].values[0]
                )
                / (monthly_trends["expense"].mean() + monthly_trends["cash_out"].mean())
            ),
        }
        findings["drifting_users_count"] = int(self.df_user_gt["is_drifting"].sum())

        return findings


def main() -> None:
    data_dir = Path("data/exports")
    figures_dir = Path("docs/data/figures/eda")
    analyzer = EDAAnalyzer(data_dir=data_dir, figures_dir=figures_dir)
    findings = analyzer.generate_figures_and_findings()
    print("[+] EDA analysis completed!")
    print(f"    - Total Txns: {findings['total_txns']:,}")
    print(f"    - Engel's Law Pearson r: {findings['pearson_engels']:.2f}")
    print(
        f"    - Freelancer income CV: {findings['freelancer_cv']:.2f} vs Govt: {findings['govt_cv']:.2f}"
    )
    print(f"    - March Expense ratio: {findings['mar_may_spikes']['mar_expense_ratio']:.2f}x")
    print(f"    - May Outflow ratio: {findings['mar_may_spikes']['may_outflow_ratio']:.2f}x")
    print(f"    - (User, Category) pairs < 10 txns: {findings['cold_start_under_10_cat_pct']:.1f}%")
    print(f"    - Drifting users: {findings['drifting_users_count']}")


if __name__ == "__main__":
    main()
