"""
evaluation.py
=============
Computes evaluation metrics for:
  - the Blue Team detector on normal (held-out) traffic
  - the Blue Team detector against each Red-Team attack family individually
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def evaluate_attack_batch(detector, attack_df: pd.DataFrame, X_attack: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
    """Given a Red-Team attack batch (with an `attack_type` column) and its
    preprocessed feature matrix X_attack (same row order), compute per-attack
    detection statistics using the given BlueTeamDetector."""
    proba = detector.predict_proba(X_attack)
    pred = (proba >= threshold).astype(int)

    out = attack_df[["attack_type"]].copy().reset_index(drop=True)
    out["risk_score"] = np.clip(np.round(proba * 100, 1), 0, 100)
    out["detected"] = pred  # since all rows here are fraud (label=1), detected==pred==1 means caught
    out["missed"] = 1 - pred

    summary = out.groupby("attack_type").agg(
        number_generated=("attack_type", "count"),
        number_detected=("detected", "sum"),
        avg_risk_score=("risk_score", "mean"),
    ).reset_index()
    summary["number_missed"] = summary["number_generated"] - summary["number_detected"]
    summary["detection_rate"] = summary["number_detected"] / summary["number_generated"]
    summary["false_negative_rate"] = summary["number_missed"] / summary["number_generated"]
    summary["avg_risk_score"] = summary["avg_risk_score"].round(2)
    summary["detection_rate"] = summary["detection_rate"].round(4)
    summary["false_negative_rate"] = summary["false_negative_rate"].round(4)

    return summary.sort_values("detection_rate"), out


def detection_rate_dict(summary: pd.DataFrame) -> dict:
    return dict(zip(summary["attack_type"], summary["detection_rate"]))


def overall_attack_metrics(per_row: pd.DataFrame) -> dict:
    return {
        "total_attacks_generated": int(len(per_row)),
        "total_detected": int(per_row["detected"].sum()),
        "total_missed": int(per_row["missed"].sum()),
        "overall_detection_rate": round(float(per_row["detected"].mean()), 4),
        "overall_avg_risk_score": round(float(per_row["risk_score"].mean()), 2),
    }
