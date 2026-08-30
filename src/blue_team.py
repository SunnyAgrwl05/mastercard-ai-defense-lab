"""
blue_team.py
============
The BLUE TEAM: trains and serves the fraud-detection model(s).

Models trained:
  - Random Forest (class-weighted)
  - Gradient Boosting (XGBoost if available, else sklearn HistGradientBoosting)
  - Isolation Forest (unsupervised anomaly detector, used as an auxiliary signal)

Final "production" model = the supervised model with the best validation
PR-AUC (Average Precision), because on an imbalanced fraud problem PR-AUC is a
far more informative selection criterion than accuracy or even ROC-AUC.

`risk_score(prob)` converts a model probability into the 0-100 scale required
by the challenge, with configurable (NOT Mastercard-production) thresholds.
"""

from __future__ import annotations

import json
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier, IsolationForest, HistGradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    average_precision_score, confusion_matrix, classification_report, roc_curve, precision_recall_curve,
)

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

RISK_BANDS = [(0, 30, "Low Risk"), (31, 60, "Medium Risk"), (61, 80, "High Risk"), (81, 100, "Critical Risk")]


def risk_score(prob: np.ndarray) -> np.ndarray:
    """Map a model fraud-probability in [0,1] to a 0-100 risk score.

    NOTE: This is a simple monotonic scaling (prob * 100) for interpretability
    in this prototype. The 0-30/31-60/61-80/81-100 bands below are
    demonstration thresholds we chose for this challenge submission, NOT
    Mastercard production risk thresholds.
    """
    return np.clip(np.round(prob * 100, 1), 0, 100)


def risk_band(score: float) -> str:
    for lo, hi, name in RISK_BANDS:
        if lo <= score <= hi:
            return name
    return "Critical Risk"


class BlueTeamDetector:
    def __init__(self, feature_names: list, seed: int = 42):
        self.feature_names = feature_names
        self.seed = seed
        self.models = {}
        self.best_model_name = None
        self.iso_forest = None

    def fit(self, X_train: pd.DataFrame, y_train: pd.Series, X_val: pd.DataFrame, y_val: pd.Series) -> dict:
        n_pos, n_neg = y_train.sum(), len(y_train) - y_train.sum()
        scale_pos_weight = n_neg / max(n_pos, 1)

        rf = RandomForestClassifier(
            n_estimators=150, max_depth=10, min_samples_leaf=3,
            class_weight="balanced_subsample", n_jobs=-1, random_state=self.seed,
        )
        rf.fit(X_train, y_train)
        self.models["random_forest"] = rf

        if HAS_XGB:
            gb = XGBClassifier(
                n_estimators=150, max_depth=4, learning_rate=0.1,
                subsample=0.85, colsample_bytree=0.85,
                scale_pos_weight=scale_pos_weight, eval_metric="aucpr",
                random_state=self.seed, n_jobs=-1,
            )
            gb.fit(X_train, y_train)
            self.models["xgboost"] = gb
        else:
            gb = HistGradientBoostingClassifier(
                max_depth=8, learning_rate=0.08, max_iter=300,
                class_weight="balanced", random_state=self.seed,
            )
            gb.fit(X_train, y_train)
            self.models["hist_gradient_boosting"] = gb

        # Unsupervised anomaly detector trained ONLY on legitimate training txns
        iso = IsolationForest(n_estimators=120, contamination=float(np.clip(y_train.mean(), 0.005, 0.05)),
                               random_state=self.seed, n_jobs=-1)
        iso.fit(X_train[y_train == 0])
        self.iso_forest = iso

        # Select best supervised model by validation PR-AUC
        val_scores = {}
        for name, model in self.models.items():
            proba = model.predict_proba(X_val)[:, 1]
            val_scores[name] = average_precision_score(y_val, proba)
        self.best_model_name = max(val_scores, key=val_scores.get)
        return val_scores

    @property
    def best_model(self):
        return self.models[self.best_model_name]

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        return self.best_model.predict_proba(X)[:, 1]

    def predict(self, X: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        return (self.predict_proba(X) >= threshold).astype(int)

    def anomaly_score(self, X: pd.DataFrame) -> np.ndarray:
        # decision_function: higher = more normal. Flip & rescale to [0,1]-ish.
        raw = -self.iso_forest.decision_function(X)
        return (raw - raw.min()) / (raw.max() - raw.min() + 1e-9)

    def evaluate(self, X: pd.DataFrame, y: pd.Series, threshold: float = 0.5) -> dict:
        proba = self.predict_proba(X)
        pred = (proba >= threshold).astype(int)
        cm = confusion_matrix(y, pred).tolist()
        metrics = {
            "model_used": self.best_model_name,
            "threshold": threshold,
            "accuracy": accuracy_score(y, pred),
            "precision": precision_score(y, pred, zero_division=0),
            "recall": recall_score(y, pred, zero_division=0),
            "f1_score": f1_score(y, pred, zero_division=0),
            "roc_auc": roc_auc_score(y, proba) if y.nunique() > 1 else float("nan"),
            "pr_auc": average_precision_score(y, proba) if y.nunique() > 1 else float("nan"),
            "confusion_matrix": cm,
            "classification_report": classification_report(y, pred, zero_division=0, output_dict=True),
            "n_samples": int(len(y)),
            "n_fraud": int(y.sum()),
        }
        return metrics

    def curves(self, X: pd.DataFrame, y: pd.Series) -> dict:
        proba = self.predict_proba(X)
        fpr, tpr, _ = roc_curve(y, proba)
        prec, rec, _ = precision_recall_curve(y, proba)
        return {"fpr": fpr.tolist(), "tpr": tpr.tolist(), "precision": prec.tolist(), "recall": rec.tolist()}

    def feature_importance(self) -> pd.Series:
        model = self.best_model
        if hasattr(model, "feature_importances_"):
            return pd.Series(model.feature_importances_, index=self.feature_names).sort_values(ascending=False)
        raise AttributeError("Best model has no feature_importances_")

    def save(self, path: str):
        joblib.dump(self, path)

    @staticmethod
    def load(path: str) -> "BlueTeamDetector":
        return joblib.load(path)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "/home/claude/mastercard-ai-defense-lab/src")
    from preprocessing import fit_transform_splits

    df = pd.read_parquet("/home/claude/mastercard-ai-defense-lab/outputs/synthetic_transactions.parquet")
    split = fit_transform_splits(df)

    detector = BlueTeamDetector(feature_names=split.feature_names)
    val_scores = detector.fit(split.X_train, split.y_train, split.X_val, split.y_val)
    print("Validation PR-AUC per model:", val_scores)
    print("Selected model:", detector.best_model_name)

    test_metrics = detector.evaluate(split.X_test, split.y_test)
    print(json.dumps({k: v for k, v in test_metrics.items() if k not in ("classification_report",)}, indent=2, default=str))

    detector.save("/home/claude/mastercard-ai-defense-lab/models/fraud_detector.pkl")
    joblib.dump(split, "/home/claude/mastercard-ai-defense-lab/models/split_data.pkl")
    print("saved model + split data.")
