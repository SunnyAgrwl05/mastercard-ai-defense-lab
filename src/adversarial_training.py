"""
adversarial_training.py
========================
Implements the closed feedback loop required by the challenge:

  NORMAL TRAINING DATA -> BLUE TEAM DETECTOR -> RED TEAM ATTACK GENERATION
  -> ATTACKED TRANSACTIONS -> BLUE TEAM DETECTION -> MISSED ATTACKS
  -> ADVERSARIAL TRAINING DATA -> RETRAIN BLUE TEAM -> RE-EVALUATE
  -> IMPROVED DEFENSE

Across multiple ROUNDS: each round the Red-Team agent adapts its personas
based on last round's per-attack detection rate (see red_team.RedTeamAgent.adapt),
and the Blue Team is retrained on (original training data + all missed attacks
accumulated so far). This produces genuine before/after metrics rather than a
single static comparison.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from preprocessing import transform_new
from blue_team import BlueTeamDetector
from red_team import RedTeamAgent, ATTACK_TYPES
from evaluation import evaluate_attack_batch, detection_rate_dict, overall_attack_metrics


def build_account_profiles(df: pd.DataFrame) -> dict:
    profiles = {}
    legit = df[df["fraud_label"] == 0]
    for acc_id, g in legit.groupby("account_id"):
        profiles[acc_id] = {
            "avg_amount": float(g["amount"].mean()),
            "std_amount": float(max(g["amount"].std(), 1.0)),
            "favourite_category": g["merchant_category"].mode().iloc[0],
            "favourite_device": g["device_type"].mode().iloc[0],
        }
    return profiles


def run_closed_loop(
    df: pd.DataFrame,
    split,
    detector: BlueTeamDetector,
    n_rounds: int = 3,
    n_per_type: int = 300,
    seed: int = 7,
) -> dict:
    """Runs the full closed loop and returns a dict with per-round diagnostics
    plus the final retrained detector."""
    legit_pool = df[df["fraud_label"] == 0]
    account_profiles = build_account_profiles(df)
    agent = RedTeamAgent(rng_seed=seed)

    round_logs = []
    accumulated_missed_raw = []  # raw (pre-feature-engineering) attack rows the model missed

    current_detector = detector
    X_train_current = split.X_train.copy()
    y_train_current = split.y_train.copy()

    # Baseline (round 0) evaluation on a fresh attack batch, before any adversarial retraining
    for round_idx in range(1, n_rounds + 1):
        attack_batch = agent.generate_attack_batch(legit_pool, n_per_type=n_per_type, account_profiles=account_profiles)
        X_attack = transform_new(attack_batch, split.scaler, split.encoder, split.feature_names)

        summary, per_row = evaluate_attack_batch(current_detector, attack_batch, X_attack)
        overall = overall_attack_metrics(per_row)
        det_rates = detection_rate_dict(summary)

        # collect missed attacks (raw rows) for adversarial retraining
        missed_mask = per_row["missed"] == 1
        missed_raw = attack_batch.loc[missed_mask.values].copy()
        accumulated_missed_raw.append(missed_raw)

        round_logs.append({
            "round": round_idx,
            "persona_state_before_adapt": agent.persona_state(),
            "attack_type_summary": summary,
            "overall": overall,
            "n_missed_this_round": int(missed_mask.sum()),
        })

        # Red team adapts its personas from what the blue team just showed it
        agent.adapt(det_rates)

        # Blue team retrains on original training data + everything missed so far
        missed_all = pd.concat(accumulated_missed_raw, ignore_index=True) if accumulated_missed_raw else pd.DataFrame()
        if len(missed_all) > 0:
            X_missed = transform_new(missed_all, split.scaler, split.encoder, split.feature_names)
            y_missed = pd.Series(np.ones(len(missed_all), dtype=int))
            X_train_current = pd.concat([split.X_train, X_missed], ignore_index=True)
            y_train_current = pd.concat([split.y_train, y_missed], ignore_index=True)

            new_detector = BlueTeamDetector(feature_names=split.feature_names, seed=42)
            new_detector.fit(X_train_current, y_train_current, split.X_val, split.y_val)
            current_detector = new_detector

    # Final post-loop evaluation: fresh, held-out attack batch (unseen combination)
    final_attack_batch = agent.generate_attack_batch(legit_pool, n_per_type=n_per_type, account_profiles=account_profiles)
    X_final_attack = transform_new(final_attack_batch, split.scaler, split.encoder, split.feature_names)
    final_summary, final_per_row = evaluate_attack_batch(current_detector, final_attack_batch, X_final_attack)
    final_overall = overall_attack_metrics(final_per_row)

    # Clean test-set comparison: original detector vs final detector, both on
    # the SAME untouched held-out test split (no attacks mixed in) to show
    # adversarial training didn't damage normal-traffic performance.
    before_test_metrics = detector.evaluate(split.X_test, split.y_test)
    after_test_metrics = current_detector.evaluate(split.X_test, split.y_test)

    return {
        "round_logs": round_logs,
        "final_attack_summary": final_summary,
        "final_overall": final_overall,
        "before_test_metrics": before_test_metrics,
        "after_test_metrics": after_test_metrics,
        "final_detector": current_detector,
        "agent_final_state": agent.persona_state(),
        "n_adversarial_rows_added": int(sum(len(x) for x in accumulated_missed_raw)),
    }


if __name__ == "__main__":
    import sys, joblib, json
    sys.path.insert(0, "/home/claude/mastercard-ai-defense-lab/src")

    df = pd.read_parquet("/home/claude/mastercard-ai-defense-lab/outputs/synthetic_transactions.parquet")
    split = joblib.load("/home/claude/mastercard-ai-defense-lab/models/split_data.pkl")
    detector = BlueTeamDetector.load("/home/claude/mastercard-ai-defense-lab/models/fraud_detector.pkl")

    results = run_closed_loop(df, split, detector, n_rounds=2, n_per_type=150)

    print("=== BEFORE (initial detector) on held-out attack batch, round 1 ===")
    print(results["round_logs"][0]["attack_type_summary"])
    print(results["round_logs"][0]["overall"])

    print("\n=== AFTER closed loop: final fresh attack batch ===")
    print(results["final_attack_summary"])
    print(results["final_overall"])

    print("\n=== Clean test-set comparison (no attacks mixed in) ===")
    print("BEFORE:", {k: v for k, v in results["before_test_metrics"].items() if k in ("precision", "recall", "f1_score", "roc_auc", "pr_auc")})
    print("AFTER :", {k: v for k, v in results["after_test_metrics"].items() if k in ("precision", "recall", "f1_score", "roc_auc", "pr_auc")})

    print("\nAdversarial rows added to training:", results["n_adversarial_rows_added"])

    results["final_detector"].save("/home/claude/mastercard-ai-defense-lab/models/fraud_detector_after_closed_loop.pkl")

    # ---- Persist everything needed for the notebook / writeup / viz ----
    out_metrics_dir = "/home/claude/mastercard-ai-defense-lab/outputs/metrics"
    results["round_logs"][0]["attack_type_summary"].to_csv(f"{out_metrics_dir}/round1_before_attack_summary.csv", index=False)
    results["final_attack_summary"].to_csv(f"{out_metrics_dir}/final_after_attack_summary.csv", index=False)
    results["agent_final_state"].to_csv(f"{out_metrics_dir}/red_team_persona_final_state.csv", index=False)

    def clean(m):
        return {k: v for k, v in m.items() if k != "classification_report"}

    with open(f"{out_metrics_dir}/closed_loop_summary.json", "w") as f:
        json.dump({
            "round1_before_overall": results["round_logs"][0]["overall"],
            "final_after_overall": results["final_overall"],
            "before_test_metrics": clean(results["before_test_metrics"]),
            "after_test_metrics": clean(results["after_test_metrics"]),
            "n_adversarial_rows_added": results["n_adversarial_rows_added"],
            "n_rounds": len(results["round_logs"]),
        }, f, indent=2, default=str)

    for i, rl in enumerate(results["round_logs"], start=1):
        rl["attack_type_summary"].to_csv(f"{out_metrics_dir}/round{i}_attack_summary.csv", index=False)

    print("saved improved detector + all metrics.")

