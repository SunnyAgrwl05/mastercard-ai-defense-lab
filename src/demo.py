"""
demo.py
=======
End-to-end demonstration required by the challenge brief:
  1. Generate a legitimate transaction.
  2. Apply a Red-Team attack to it.
  3. Run the Blue-Team detector.
  4. Show prediction + risk score + plain-English explanation.
  5. If missed, add it to the adversarial set and retrain, then re-run the
     SAME attack to show whether detection improved.

Exposes two functions matching the brief's required signatures:
    simulate_attack(transaction: dict, attack_type: str) -> dict
    detect_transaction(transaction: dict) -> dict
"""
from __future__ import annotations

import sys
import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, "/home/claude/mastercard-ai-defense-lab/src")
from preprocessing import transform_new
from blue_team import BlueTeamDetector, risk_band
from red_team import RedTeamAgent
from explainability import Explainer

BASE = "/home/claude/mastercard-ai-defense-lab"

_split = joblib.load(f"{BASE}/models/split_data.pkl")
_detector = BlueTeamDetector.load(f"{BASE}/models/fraud_detector_after_closed_loop.pkl")
_agent = RedTeamAgent(rng_seed=99)
_explainer = Explainer(_detector, background=_split.X_train)


def simulate_attack(transaction: dict, attack_type: str) -> dict:
    """Apply one Red-Team attack family to a base transaction dict."""
    return _agent.craft_attack(dict(transaction), attack_type)


def detect_transaction(transaction: dict, detector: BlueTeamDetector = None) -> dict:
    """Run the Blue-Team detector (and explainer) on a single transaction dict."""
    det = detector or _detector
    row_df = pd.DataFrame([transaction])
    X = transform_new(row_df, _split.scaler, _split.encoder, _split.feature_names)
    explanation = Explainer(det, background=_split.X_train).explain_row(X) if detector is not None else _explainer.explain_row(X)
    explanation["risk_band"] = risk_band(explanation["risk_score"])
    return explanation


def run_full_demo():
    df = pd.read_parquet(f"{BASE}/outputs/synthetic_transactions.parquet")
    base_txn = df[df["fraud_label"] == 0].sample(1, random_state=123).iloc[0].to_dict()
    print("1) Base legitimate transaction (sampled from synthetic data):")
    print({k: base_txn[k] for k in ["amount", "merchant_category", "geo_distance_km", "device_type"]})

    attack_type = "amount_manipulation"
    attacked = simulate_attack(base_txn, attack_type)
    print(f"\n2) Red-Team applies '{attack_type}' attack:")
    print({k: attacked[k] for k in ["amount", "merchant_category", "geo_distance_km", "device_type"]})

    print("\n3) Blue-Team (BEFORE closed-loop detector) evaluates it:")
    before_detector = BlueTeamDetector.load(f"{BASE}/models/fraud_detector.pkl")
    result_before = detect_transaction(attacked, detector=before_detector)
    print(result_before["narrative"])

    print("\n4) Blue-Team (AFTER closed-loop detector) evaluates the SAME attack:")
    result_after = detect_transaction(attacked)
    print(result_after["narrative"])

    print("\n5) Comparison:")
    print(f"   Risk score before closed-loop training: {result_before['risk_score']}")
    print(f"   Risk score after  closed-loop training: {result_after['risk_score']}")
    improved = result_after["risk_score"] > result_before["risk_score"]
    print(f"   Detection improved after closed-loop adversarial training: {improved}")
    return {"before": result_before, "after": result_after, "improved": improved}


if __name__ == "__main__":
    run_full_demo()
