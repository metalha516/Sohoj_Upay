"""Production Inference Engine and Secure Artifact Loader for Model A (Behavior Classification).

Features:
1. SHA-256 Checksum validation before model deserialization to prevent artifact tampering.
2. Scale-invariant dimensionless feature extraction.
3. Cold-start detection (< 2 months activity returns 'insufficient_data').
4. Non-judgmental human-readable top factors for explainability.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from ml.training.dataset import extract_features_from_dict


class SecurityError(Exception):
    """Raised when an artifact fails cryptographic integrity checks."""


@dataclass
class FactorDetail:
    feature: str
    value: float
    direction: str
    label: str


@dataclass
class BehaviorPrediction:
    profile: str
    confidence: float
    top_factors: list[dict[str, Any]]
    class_probabilities: dict[str, float] = field(default_factory=dict)
    is_cold_start: bool = False
    model_version: str = "v1.0.0"


class BehaviorClassifier:
    """Production inference engine for Model A."""

    def __init__(
        self,
        calibrated_model: Any,
        base_estimator: Any,
        classes: list[str],
        feature_names: list[str],
        model_version: str = "v1.0.0",
        feature_schema_version: str = "v1.0.0",
        sha256_checksum: str = "",
    ):
        self.calibrated_model = calibrated_model
        self.base_estimator = base_estimator
        self.classes = classes
        self.feature_names = feature_names
        self.model_version = model_version
        self.feature_schema_version = feature_schema_version
        self.sha256_checksum = sha256_checksum

    @classmethod
    def load(
        cls,
        model_path: Path | str,
        metadata_path: Path | str | None = None,
    ) -> BehaviorClassifier:
        """Load and cryptographically verify model artifact before deserialization."""
        m_path = Path(model_path)
        if not m_path.exists():
            raise FileNotFoundError(f"Model artifact not found: {m_path}")

        meta_p = (
            Path(metadata_path)
            if metadata_path is not None
            else m_path.parent / f"{m_path.stem}_metadata.json"
        )
        if not meta_p.exists():
            raise FileNotFoundError(f"Metadata file not found: {meta_p}")

        with open(meta_p, encoding="utf-8") as f:
            metadata = json.load(f)

        expected_checksum = metadata.get("sha256_checksum", "")
        # Compute SHA-256 of the model file
        h = hashlib.sha256()
        with open(m_path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        actual_checksum = h.hexdigest()

        if actual_checksum != expected_checksum:
            raise SecurityError(
                f"Model artifact integrity check failed! Expected {expected_checksum}, "
                f"got {actual_checksum}. Deserialization aborted."
            )

        # Safe deserialization
        package = joblib.load(m_path)
        return cls(
            calibrated_model=package["calibrated_model"],
            base_estimator=package["base_estimator"],
            classes=package["classes"],
            feature_names=package["feature_names"],
            model_version=metadata.get("model_version", "v1.0.0"),
            feature_schema_version=metadata.get("feature_schema_version", "v1.0.0"),
            sha256_checksum=actual_checksum,
        )

    def predict(
        self,
        features: dict[str, Any],
        months_active: int = 12,
    ) -> BehaviorPrediction:
        """Classify user financial behavior from monthly feature dictionary or object.

        Handles cold start (< 2 months) by emitting 'insufficient_data'.
        """
        # 1. Cold start policy (< 2 months active)
        if months_active < 2:
            return BehaviorPrediction(
                profile="insufficient_data",
                confidence=0.0,
                top_factors=[
                    {
                        "feature": "months_active",
                        "value": months_active,
                        "direction": "low",
                        "label": f"History too short ({months_active} month(s) observed, minimum 2 required)",
                    }
                ],
                is_cold_start=True,
                model_version=self.model_version,
            )

        # 2. Extract dimensionless, scale-invariant feature vector
        feat_vec = extract_features_from_dict(features)
        X = feat_vec.reshape(1, -1)

        # 3. Predict calibrated class probabilities
        probs = self.calibrated_model.predict_proba(X)[0]
        pred_idx = int(np.argmax(probs))
        profile = self.classes[pred_idx]
        confidence = float(round(probs[pred_idx], 4))

        prob_dict = {cls_name: float(round(probs[i], 4)) for i, cls_name in enumerate(self.classes)}

        # 4. Generate explainable top factors
        top_factors = self.explain(features, profile)

        return BehaviorPrediction(
            profile=profile,
            confidence=confidence,
            top_factors=top_factors,
            class_probabilities=prob_dict,
            is_cold_start=False,
            model_version=self.model_version,
        )

    def predict_batch(
        self,
        features_list: list[dict[str, Any]] | pd.DataFrame,
        months_active: int = 12,
    ) -> list[BehaviorPrediction]:
        """Vectorized batch prediction across multiple monthly records."""
        if isinstance(features_list, pd.DataFrame):
            records = features_list.to_dict(orient="records")
        else:
            records = list(features_list)

        if not records:
            return []

        if months_active < 2:
            return [self.predict(rec, months_active=months_active) for rec in records]

        X_mat = np.array([extract_features_from_dict(rec) for rec in records], dtype=np.float64)
        all_probs = self.calibrated_model.predict_proba(X_mat)
        pred_indices = np.argmax(all_probs, axis=1)

        results = []
        for i, rec in enumerate(records):
            probs = all_probs[i]
            idx = int(pred_indices[i])
            prof = self.classes[idx]
            conf = float(round(probs[idx], 4))
            p_dict = {c_name: float(round(probs[j], 4)) for j, c_name in enumerate(self.classes)}
            factors = self.explain(rec, prof)
            results.append(
                BehaviorPrediction(
                    profile=prof,
                    confidence=conf,
                    top_factors=factors,
                    class_probabilities=p_dict,
                    is_cold_start=False,
                    model_version=self.model_version,
                )
            )
        return results

    def explain(
        self,
        features: dict[str, Any],
        predicted_profile: str,
        max_factors: int = 3,
    ) -> list[dict[str, Any]]:
        """Generate human-readable, non-judgmental explanations for the prediction."""
        factors: list[dict[str, Any]] = []

        sr = float(features.get("savings_rate") or 0.0)
        rolling_sr = float(features.get("rolling_savings_rate_3m_mean") or sr)
        txn_cnt = max(float(features.get("txn_count") or 1.0), 1.0)
        c_cnt = float(features.get("cashout_count") or 0.0)
        cashout_ratio = c_cnt / txn_cnt
        nec_rate = float(features.get("necessity_rate") or 0.0)
        disc_rate = float(features.get("discretionary_rate") or 0.0)
        avg_t = max(float(features.get("avg_txn") or 1.0), 1.0)
        exp_v = max(float(features.get("expense_variance") or 0.0), 0.0)
        vol_cv = float(np.sqrt(exp_v) / avg_t)
        ie_ratio = float(features.get("income_expense_ratio") or 1.0)

        if predicted_profile == "consistent_saver":
            factors.append(
                {
                    "feature": "rolling_sr_mean",
                    "value": round(rolling_sr, 2),
                    "direction": "high",
                    "label": f"Savings rate: high ({rolling_sr * 100:.1f}%)",
                }
            )
            factors.append(
                {
                    "feature": "necessity_rate",
                    "value": round(nec_rate, 2),
                    "direction": "moderate",
                    "label": f"Necessity expense share: moderate ({nec_rate * 100:.1f}%)",
                }
            )
            factors.append(
                {
                    "feature": "income_expense_ratio",
                    "value": round(ie_ratio, 2),
                    "direction": "surplus",
                    "label": f"Income-to-expense buffer: healthy ({ie_ratio:.2f}x)",
                }
            )

        elif predicted_profile == "tight_budgeter":
            factors.append(
                {
                    "feature": "necessity_rate",
                    "value": round(nec_rate, 2),
                    "direction": "high",
                    "label": f"Necessity expense share: high ({nec_rate * 100:.1f}%)",
                }
            )
            factors.append(
                {
                    "feature": "savings_rate",
                    "value": round(sr, 2),
                    "direction": "low",
                    "label": f"Savings rate: limited ({sr * 100:.1f}%)",
                }
            )
            factors.append(
                {
                    "feature": "discretionary_rate",
                    "value": round(disc_rate, 2),
                    "direction": "low",
                    "label": f"Discretionary expense share: lean ({disc_rate * 100:.1f}%)",
                }
            )

        elif predicted_profile == "cash_dominant_transactor":
            factors.append(
                {
                    "feature": "cashout_frequency",
                    "value": round(cashout_ratio, 2),
                    "direction": "high",
                    "label": f"Cash-out frequency: high ({cashout_ratio * 100:.1f}% of transactions)",
                }
            )
            factors.append(
                {
                    "feature": "cashout_count",
                    "value": int(c_cnt),
                    "direction": "high",
                    "label": f"Monthly cash-outs: {int(c_cnt)} withdrawals",
                }
            )
            factors.append(
                {
                    "feature": "necessity_rate",
                    "value": round(nec_rate, 2),
                    "direction": "high",
                    "label": f"Necessity expense share: {nec_rate * 100:.1f}%",
                }
            )

        elif predicted_profile == "discretionary_spender":
            factors.append(
                {
                    "feature": "discretionary_rate",
                    "value": round(disc_rate, 2),
                    "direction": "high",
                    "label": f"Discretionary expense share: elevated ({disc_rate * 100:.1f}%)",
                }
            )
            factors.append(
                {
                    "feature": "savings_rate",
                    "value": round(sr, 2),
                    "direction": "moderate",
                    "label": f"Savings rate: {sr * 100:.1f}%",
                }
            )

        elif predicted_profile == "volatile_earner":
            factors.append(
                {
                    "feature": "expense_cv",
                    "value": round(vol_cv, 2),
                    "direction": "high",
                    "label": f"Expenditure volatility: high (CV = {vol_cv:.2f})",
                }
            )
            factors.append(
                {
                    "feature": "spending_growth",
                    "value": round(float(features.get("spending_growth") or 0.0), 2),
                    "direction": "fluctuating",
                    "label": "Month-over-month growth swings observed",
                }
            )

        else:  # balanced_spender
            factors.append(
                {
                    "feature": "savings_rate",
                    "value": round(sr, 2),
                    "direction": "balanced",
                    "label": f"Savings rate: balanced ({sr * 100:.1f}%)",
                }
            )
            factors.append(
                {
                    "feature": "necessity_rate",
                    "value": round(nec_rate, 2),
                    "direction": "balanced",
                    "label": f"Necessity expense share: balanced ({nec_rate * 100:.1f}%)",
                }
            )
            factors.append(
                {
                    "feature": "discretionary_rate",
                    "value": round(disc_rate, 2),
                    "direction": "moderate",
                    "label": f"Discretionary expense share: controlled ({disc_rate * 100:.1f}%)",
                }
            )

        return factors[:max_factors]
