"""
explainability.py
==================
Explains individual fraud-risk predictions:
  1. Global feature importance (model-native, always available).
  2. SHAP local explanations (if the installed shap version supports the
     underlying model type — this is checked at runtime, never assumed).
  3. A judge-friendly PLAIN-ENGLISH risk narrative generated from a small
     rule-based template engine over the top contributing features — this is
     the piece a non-technical reviewer can read without knowing what SHAP is.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False


FEATURE_LABELS = {
    "amount": "transaction amount",
    "amount_log": "transaction amount (log-scaled)",
    "merchant_risk_score": "merchant category risk",
    "geo_distance_km": "distance from home location",
    "account_age_days": "account age",
    "failed_txn_count_recent": "recent failed-transaction count",
    "seconds_since_prev_txn": "time gap since previous transaction",
    "txn_count_last_1h": "transaction count in the last hour",
    "txn_count_last_24h": "transaction count in the last 24 hours",
    "amount_avg_last_5": "recent average spend",
    "amount_deviation_ratio": "deviation from recent average spend",
    "is_new_device_hint": "new/unrecognized device signal",
    "hour_of_day": "time of day",
    "day_of_week": "day of week",
    "is_weekend": "weekend timing",
    "velocity_score": "overall transaction velocity",
    "is_high_risk_merchant": "high-risk merchant category flag",
    "is_far_from_home": "far-from-home flag",
    "rapid_repeat_txn": "rapid repeat-transaction flag",
}


def _friendly_name(feat: str) -> str:
    if feat in FEATURE_LABELS:
        return FEATURE_LABELS[feat]
    for prefix, label in [("merchant_category_", "merchant category: "),
                           ("device_type_", "device type: "),
                           ("payment_method_", "payment method: ")]:
        if feat.startswith(prefix):
            return label + feat[len(prefix):]
    return feat.replace("_", " ")


class Explainer:
    def __init__(self, detector, background: pd.DataFrame | None = None, max_background: int = 200):
        self.detector = detector
        self.shap_explainer = None
        if HAS_SHAP:
            try:
                # tree_path_dependent avoids the background-dataset interventional
                # path, which newer shap versions reject for XGBoost models with
                # any categorical-style split metadata (raises NotImplementedError).
                self.shap_explainer = shap.TreeExplainer(detector.best_model, feature_perturbation="tree_path_dependent")
            except Exception:
                self.shap_explainer = None

    def global_importance(self, top_n: int = 15) -> pd.DataFrame:
        imp = self.detector.feature_importance().head(top_n)
        return pd.DataFrame({
            "feature": imp.index,
            "friendly_name": [_friendly_name(f) for f in imp.index],
            "importance": imp.values,
        })

    def explain_row(self, X_row: pd.DataFrame, top_n: int = 4) -> dict:
        """X_row: single-row DataFrame with the model's feature columns."""
        proba = float(self.detector.predict_proba(X_row)[0])
        risk = round(proba * 100, 1)

        contributions = None
        if self.shap_explainer is not None:
            try:
                sv = self.shap_explainer.shap_values(X_row)
                sv = sv[1][0] if isinstance(sv, list) else np.array(sv)[0]
                contributions = pd.Series(sv, index=X_row.columns)
            except Exception:
                contributions = None

        if contributions is None:
            # fallback: feature_importance * standardized feature value magnitude
            gi = self.detector.feature_importance()
            contributions = gi.reindex(X_row.columns).fillna(0) * X_row.iloc[0].abs()

        top_features = contributions.sort_values(ascending=False).head(top_n)
        signals = [_friendly_name(f) for f in top_features.index]

        narrative = self._build_narrative(risk, proba, signals)
        return {
            "risk_score": risk,
            "fraud_probability": round(proba, 4),
            "prediction": "Fraud" if proba >= 0.5 else "Legitimate",
            "top_signals": signals,
            "narrative": narrative,
        }

    @staticmethod
    def _build_narrative(risk: float, proba: float, signals: list) -> str:
        if risk >= 81:
            band = "Critical Risk"
            lead = "This transaction shows strong, multiple indicators consistent with fraud."
        elif risk >= 61:
            band = "High Risk"
            lead = "This transaction shows several notable signals associated with fraud."
        elif risk >= 31:
            band = "Medium Risk"
            lead = "This transaction shows some signals worth a closer look, but is not clearly fraudulent."
        else:
            band = "Low Risk"
            lead = "This transaction looks broadly consistent with normal account behaviour."

        if signals:
            sig_text = ", ".join(signals[:-1]) + (f", and {signals[-1]}" if len(signals) > 1 else signals[0])
        else:
            sig_text = "no single dominant factor"

        return (f"Risk Score: {risk}/100 ({band}). {lead} "
                f"The main contributing signals were: {sig_text}.")
