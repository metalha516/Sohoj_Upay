"""Baseline evaluation pipeline computing empirical benchmark metrics on validation data."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from ml.models.baselines import (
    ExpenseForecasterBaseline,
    RobustZScoreAnomalyDetector,
    RuleBasedBehaviorClassifier,
)
from ml.preprocessing.run_eda import EDAAnalyzer


@dataclass
class BaselineEvaluationReport:
    # Classifier metrics
    classifier_accuracy: float
    classifier_macro_f1: float
    classifier_macro_precision: float
    classifier_macro_recall: float
    classifier_report: str

    # Anomaly metrics
    anomaly_precision: float
    anomaly_recall: float
    anomaly_f1: float
    anomaly_roc_auc: float

    # Forecaster metrics
    naive_mae: float
    naive_rmse: float
    naive_smape: float
    sma_mae: float
    sma_rmse: float
    sma_smape: float


def compute_smape(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Calculate Symmetric Mean Absolute Percentage Error (sMAPE)."""
    denom = np.abs(actual) + np.abs(predicted)
    valid = denom > 0
    if not np.any(valid):
        return 0.0
    return float(np.mean(200.0 * np.abs(actual[valid] - predicted[valid]) / denom[valid]))


class BaselineEvaluator:
    """Evaluates rule-based baselines across standardized train/val splits."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.analyzer = EDAAnalyzer(data_dir=data_dir, figures_dir=Path("docs/data/figures/eda"))
        self.monthly_df = self.analyzer.compute_monthly_aggregations()
        self.df_txns = self.analyzer.df_txns
        self.df_user_gt = self.analyzer.df_user_gt
        self.df_txn_gt = self.analyzer.df_txn_gt

    def split_users(self, val_size: float = 0.30, seed: int = 42) -> tuple[list[str], list[str]]:
        """Stratified user-level split ensuring 0 cross-month leakage between train and val."""
        users = self.df_user_gt["user_id"].astype(str).to_numpy()
        personas = self.df_user_gt["true_persona"].astype(str).to_numpy()
        train_u, val_u = train_test_split(
            users, test_size=val_size, random_state=seed, stratify=personas
        )
        return list(train_u), list(val_u)

    def evaluate_behavior_classifier(
        self, val_users: list[str]
    ) -> tuple[float, float, float, float, str]:
        """Evaluate RuleBasedBehaviorClassifier on validation users."""
        clf = RuleBasedBehaviorClassifier()
        val_df = self.monthly_df[self.monthly_df["user_id"].isin(val_users)].copy()

        # Only evaluate non-mixed established months (month >= 3)
        eval_records = val_df[
            (val_df["month"] >= 3) & (val_df["true_persona"] != "mixed_drifting")
        ].copy()

        y_true = eval_records["true_persona"].values
        y_pred = []

        for _, row in eval_records.iterrows():
            pred = clf.predict(
                savings_rate=float(row["savings_rate"]),
                cashout_ratio=float(row["cashout_ratio"]),
                cashout_count=float(row["cashout_count"]),
                necessity_share=float(row["necessity_share"]),
                discretionary_share=float(row["discretionary_share"]),
                months_active=int(row["month"]),
            )
            y_pred.append(pred.profile)

        acc = float(accuracy_score(y_true, y_pred))
        macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
        macro_prec = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
        macro_rec = float(recall_score(y_true, y_pred, average="macro", zero_division=0))
        report_str = classification_report(y_true, y_pred, zero_division=0)

        return acc, macro_f1, macro_prec, macro_rec, report_str

    def evaluate_anomaly_detector(
        self, val_users: list[str], max_sample: int = 25000
    ) -> tuple[float, float, float, float]:
        """Evaluate RobustZScoreAnomalyDetector against ground-truth injected transaction anomalies."""
        detector = RobustZScoreAnomalyDetector(z_threshold=3.5, min_history_samples=8)

        # Merge anomaly labels
        anomaly_ids = set(self.df_txn_gt["transaction_id"])
        val_txns = self.df_txns[
            self.df_txns["user_id"].isin(val_users) & (self.df_txns["txn_type"] == "expense")
        ].copy()

        if len(val_txns) > max_sample:
            val_txns = val_txns.sample(n=max_sample, random_state=42)

        # Precompute category user histories
        cat_histories: dict[tuple[str, str], list[float]] = {}
        for (u, cat), group in self.df_txns[self.df_txns["txn_type"] == "expense"].groupby(
            ["user_id", "category"]
        ):
            cat_histories[(str(u), str(cat))] = group["amount"].astype(float).tolist()

        # Category peer medians
        cat_peer_medians = (
            self.df_txns[self.df_txns["txn_type"] == "expense"]
            .groupby("category")["amount"]
            .median()
            .to_dict()
        )
        cat_peer_mads = (
            self.df_txns[self.df_txns["txn_type"] == "expense"]
            .groupby("category")["amount"]
            .apply(lambda s: float(np.median(np.abs(s - np.median(s)))))
            .to_dict()
        )

        y_true = []
        y_pred = []
        scores = []

        for _, row in val_txns.iterrows():
            txn_id = row["id"]
            u_id = str(row["user_id"])
            cat = str(row["category"])
            amt = float(row["amount"])

            is_gt_anomaly = txn_id in anomaly_ids
            y_true.append(1 if is_gt_anomaly else 0)

            hist = cat_histories.get((u_id, cat), [])
            peer_med = float(cat_peer_medians.get(cat, 500.0))
            peer_mad = float(cat_peer_mads.get(cat, 150.0))

            res = detector.detect(
                amount=amt, user_history=hist, peer_median=peer_med, peer_mad=peer_mad
            )
            y_pred.append(1 if res.is_anomaly else 0)
            scores.append(res.score)

        prec = float(precision_score(y_true, y_pred, zero_division=0))
        rec = float(recall_score(y_true, y_pred, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, zero_division=0))
        auc = float(roc_auc_score(y_true, scores)) if len(set(y_true)) > 1 else 0.5

        return prec, rec, f1, auc

    def evaluate_expense_forecasters(
        self, val_users: list[str]
    ) -> tuple[float, float, float, float, float, float]:
        """Evaluate Naive and 3-Month Moving Average forecasters on months 10, 11, 12."""
        forecaster = ExpenseForecasterBaseline()
        val_df = self.monthly_df[self.monthly_df["user_id"].isin(val_users)].copy()

        naive_actuals, naive_preds = [], []
        sma_actuals, sma_preds = [], []

        for u in val_users:
            u_months = val_df[val_df["user_id"] == u].sort_values("month")
            monthly_outflows = u_months.set_index("month")["monthly_outflow"].to_dict()

            # Predict months 10, 11, 12
            for target_m in (10, 11, 12):
                if target_m not in monthly_outflows:
                    continue
                actual = float(monthly_outflows[target_m])

                # History prior to target month
                hist = [
                    float(monthly_outflows[m]) for m in range(1, target_m) if m in monthly_outflows
                ]
                if not hist:
                    continue

                naive_res = forecaster.predict_naive(hist)
                sma_res = forecaster.predict_moving_average(hist, window=3)

                naive_actuals.append(actual)
                naive_preds.append(naive_res.forecast)

                sma_actuals.append(actual)
                sma_preds.append(sma_res.forecast)

        # Compute metrics
        n_act, n_pred = np.array(naive_actuals), np.array(naive_preds)
        s_act, s_pred = np.array(sma_actuals), np.array(sma_preds)

        naive_mae = float(mean_absolute_error(n_act, n_pred))
        naive_rmse = float(np.sqrt(mean_squared_error(n_act, n_pred)))
        naive_smape = compute_smape(n_act, n_pred)

        sma_mae = float(mean_absolute_error(s_act, s_pred))
        sma_rmse = float(np.sqrt(mean_squared_error(s_act, s_pred)))
        sma_smape = compute_smape(s_act, s_pred)

        return naive_mae, naive_rmse, naive_smape, sma_mae, sma_rmse, sma_smape

    def run_all_evaluations(self) -> BaselineEvaluationReport:
        """Execute full benchmark evaluation suite."""
        train_users, val_users = self.split_users(val_size=0.30, seed=42)

        acc, macro_f1, prec, rec, report = self.evaluate_behavior_classifier(val_users)
        anom_prec, anom_rec, anom_f1, anom_auc = self.evaluate_anomaly_detector(val_users)
        n_mae, n_rmse, n_smape, s_mae, s_rmse, s_smape = self.evaluate_expense_forecasters(
            val_users
        )

        return BaselineEvaluationReport(
            classifier_accuracy=acc,
            classifier_macro_f1=macro_f1,
            classifier_macro_precision=prec,
            classifier_macro_recall=rec,
            classifier_report=report,
            anomaly_precision=anom_prec,
            anomaly_recall=anom_rec,
            anomaly_f1=anom_f1,
            anomaly_roc_auc=anom_auc,
            naive_mae=n_mae,
            naive_rmse=n_rmse,
            naive_smape=n_smape,
            sma_mae=s_mae,
            sma_rmse=s_rmse,
            sma_smape=s_smape,
        )


def main() -> None:
    evaluator = BaselineEvaluator(data_dir=Path("data/exports"))
    report = evaluator.run_all_evaluations()

    print("=================================================================")
    print("           BASELINE EVALUATION BENCHMARK METRICS                 ")
    print("=================================================================")
    print("\n1. Behavior Classifier Baseline (Rule-Based Thresholds):")
    print(f"   - Accuracy:        {report.classifier_accuracy * 100:.2f}%")
    print(f"   - Macro F1:        {report.classifier_macro_f1:.4f}")
    print(f"   - Macro Precision: {report.classifier_macro_precision:.4f}")
    print(f"   - Macro Recall:    {report.classifier_macro_recall:.4f}")
    print(f"\nClassification Report:\n{report.classifier_report}")

    print("\n2. Anomaly Detection Baseline (Robust Z-Score / MAD):")
    print(f"   - Precision:       {report.anomaly_precision * 100:.2f}%")
    print(f"   - Recall:          {report.anomaly_recall * 100:.2f}%")
    print(f"   - F1-Score:        {report.anomaly_f1:.4f}")
    print(f"   - ROC-AUC:         {report.anomaly_roc_auc:.4f}")

    print("\n3. Expense Forecasting Baselines (Validation Months 10-12):")
    print(
        f"   - Naive Baseline:  MAE = BDT {report.naive_mae:,.2f} | RMSE = BDT {report.naive_rmse:,.2f} | sMAPE = {report.naive_smape:.2f}%"
    )
    print(
        f"   - 3-Month SMA:     MAE = BDT {report.sma_mae:,.2f} | RMSE = BDT {report.sma_rmse:,.2f} | sMAPE = {report.sma_smape:.2f}%"
    )
    print("=================================================================")


if __name__ == "__main__":
    main()
