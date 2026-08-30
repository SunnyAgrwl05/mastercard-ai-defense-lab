"""
red_team.py
===========
The RED TEAM: an adversarial attack-simulation engine that crafts realistic,
GenAI-style fraud attempts against the Blue-Team detector.

Design note on "GenAI-powered": we do not call any paid/external LLM API
(the challenge explicitly discourages paid-API dependencies for a
reproducible Kaggle submission). Instead we implement an **adaptive
attack-persona agent**: a parametrized generator whose parameters
(intensity, stealth-bias, feature-perturbation weights) are themselves
evolved round-over-round using the Blue-Team's OWN feedback (its miss-rate
per attack family), via a simple hill-climbing / bandit-style update. This
reproduces the *spirit* of a generative adversarial fraud actor -- attacks
that adapt to what a defense is currently missing -- without requiring any
external LLM API key. This is documented honestly in the writeup as a
heuristic adaptive agent, not a claim of using a hosted LLM.

Seven attack families are implemented, matching real payment-fraud TTPs:
  1. amount_manipulation      - shave amounts just under common auth thresholds
  2. velocity_attack          - burst of rapid transactions
  3. merchant_switching       - spread fraud across many merchants quickly
  4. geo_evasion              - keep synthetic distance low despite real ATO
  5. account_takeover         - sudden device+location+amount+velocity shift
  6. low_and_slow             - many small transactions under alerting radar
  7. behavioral_mimicry       - clone the account's own historical pattern
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass, field

ATTACK_TYPES = [
    "amount_manipulation", "velocity_attack", "merchant_switching",
    "geo_evasion", "account_takeover", "low_and_slow", "behavioral_mimicry",
]

COMMON_AUTH_THRESHOLDS = [50, 100, 200, 500, 1000, 2000, 5000]


@dataclass
class AttackPersona:
    """Mutable adversarial-agent parameters for one attack family.
    `intensity` in [0,1]: how aggressive/obvious the attack is.
    `stealth_bias` in [0,1]: how much the agent biases toward blending in.
    """
    attack_type: str
    intensity: float = 0.5
    stealth_bias: float = 0.5
    rounds_played: int = 0
    history: list = field(default_factory=list)  # detection-rate per round


class RedTeamAgent:
    def __init__(self, rng_seed: int = 7):
        self.rng = np.random.default_rng(rng_seed)
        self.personas = {a: AttackPersona(attack_type=a) for a in ATTACK_TYPES}

    # ---------- individual attack crafters ----------
    def _amount_manipulation(self, txn: dict, persona: AttackPersona) -> dict:
        t = txn.copy()
        threshold = self.rng.choice(COMMON_AUTH_THRESHOLDS)
        shave = self.rng.uniform(0.01, 0.15) * (1 - persona.stealth_bias * 0.5)
        t["amount"] = round(max(1.0, threshold * (1 - shave)), 2)
        t["amount_deviation_ratio"] = t["amount"] / max(t.get("amount_avg_last_5", t["amount"]), 1)
        return t

    def _velocity_attack(self, txn: dict, persona: AttackPersona) -> dict:
        t = txn.copy()
        burst = int(3 + persona.intensity * 15)
        t["txn_count_last_1h"] = int(t.get("txn_count_last_1h", 0) + burst)
        t["txn_count_last_24h"] = int(t.get("txn_count_last_24h", 0) + burst * self.rng.integers(1, 4))
        t["seconds_since_prev_txn"] = max(1.0, 60 * (1 - persona.intensity))
        return t

    def _merchant_switching(self, txn: dict, persona: AttackPersona) -> dict:
        t = txn.copy()
        cats = ["electronics", "crypto_exchange", "jewelry", "gambling", "money_transfer",
                "online_retail", "travel"]
        t["merchant_category"] = self.rng.choice(cats)
        t["merchant_risk_score"] = float(np.clip(self.rng.uniform(0.15, 0.4) * (1 - persona.stealth_bias * 0.4), 0.02, 0.9))
        return t

    def _geo_evasion(self, txn: dict, persona: AttackPersona) -> dict:
        t = txn.copy()
        # Real ATO would be far away; the evasive attacker fakes proximity via
        # VPN / device spoofing so geo_distance_km looks small despite fraud.
        t["geo_distance_km"] = round(float(self.rng.uniform(0.5, 15) * (1 - persona.intensity * 0.3)), 2)
        return t

    def _account_takeover(self, txn: dict, persona: AttackPersona) -> dict:
        t = txn.copy()
        t["device_type"] = self.rng.choice(["web_chrome", "mobile_app", "web_safari"])
        t["geo_distance_km"] = round(float(self.rng.uniform(200, 3000) * (1 - persona.stealth_bias * 0.3)), 2)
        t["amount"] = round(max(1.0, t["amount"] * self.rng.uniform(2.0, 6.0) * (1 - persona.stealth_bias * 0.3)), 2)
        t["txn_count_last_1h"] = int(t.get("txn_count_last_1h", 0) + int(2 + persona.intensity * 6))
        t["failed_txn_count_recent"] = int(t.get("failed_txn_count_recent", 0) + self.rng.integers(1, 4))
        return t

    def _low_and_slow(self, txn: dict, persona: AttackPersona) -> dict:
        t = txn.copy()
        cap = 15 * (1 + persona.stealth_bias)  # tries to stay well under common micro-fraud alert caps
        t["amount"] = round(float(self.rng.uniform(0.5, cap)), 2)
        t["txn_count_last_24h"] = int(t.get("txn_count_last_24h", 0) + int(1 + persona.intensity * 3))
        t["seconds_since_prev_txn"] = float(self.rng.uniform(1800, 21600))  # spaced out, not bursty
        return t

    def _behavioral_mimicry(self, txn: dict, persona: AttackPersona, account_profile: dict | None) -> dict:
        t = txn.copy()
        if account_profile:
            t["amount"] = round(float(np.clip(
                self.rng.normal(account_profile.get("avg_amount", t["amount"]), account_profile.get("std_amount", t["amount"] * 0.2)),
                1, 1e6)), 2)
            t["merchant_category"] = account_profile.get("favourite_category", t["merchant_category"])
            t["device_type"] = account_profile.get("favourite_device", t["device_type"])
        # Mimicry deliberately keeps most signals normal but sneaks in one tell:
        t["failed_txn_count_recent"] = int(t.get("failed_txn_count_recent", 0) + (1 if self.rng.random() < 0.4 else 0))
        return t

    def craft_attack(self, txn: dict, attack_type: str, account_profile: dict | None = None) -> dict:
        persona = self.personas[attack_type]
        fn = {
            "amount_manipulation": self._amount_manipulation,
            "velocity_attack": self._velocity_attack,
            "merchant_switching": self._merchant_switching,
            "geo_evasion": self._geo_evasion,
            "account_takeover": self._account_takeover,
            "low_and_slow": self._low_and_slow,
        }.get(attack_type)
        if attack_type == "behavioral_mimicry":
            attacked = self._behavioral_mimicry(txn, persona, account_profile)
        else:
            attacked = fn(txn, persona)
        attacked["attack_type"] = attack_type
        attacked["attack_intensity"] = round(persona.intensity, 3)
        attacked["fraud_label"] = 1
        return attacked

    def generate_attack_batch(self, base_df: pd.DataFrame, n_per_type: int = 400,
                               account_profiles: dict | None = None) -> pd.DataFrame:
        """Sample legitimate-looking base transactions and turn them into
        attacks for every attack family."""
        rows = []
        base_sample = base_df.sample(n=min(len(base_df), n_per_type * len(ATTACK_TYPES)),
                                      replace=len(base_df) < n_per_type * len(ATTACK_TYPES),
                                      random_state=int(self.rng.integers(0, 1_000_000)))
        base_records = base_sample.to_dict("records")
        idx = 0
        for attack_type in ATTACK_TYPES:
            for _ in range(n_per_type):
                base_txn = base_records[idx % len(base_records)]
                idx += 1
                profile = None
                if account_profiles is not None:
                    profile = account_profiles.get(base_txn.get("account_id"))
                attacked = self.craft_attack(dict(base_txn), attack_type, profile)
                attacked["original_amount"] = base_txn["amount"]
                attacked["original_geo_distance_km"] = base_txn.get("geo_distance_km")
                rows.append(attacked)
        return pd.DataFrame(rows)

    def adapt(self, detection_rate_by_type: dict):
        """Update each persona based on how well the Blue Team detected it
        last round: if detection rate is HIGH, the agent increases stealth_bias
        and searches a different intensity to evade; if detection is LOW
        (attack is already working), it keeps exploiting with slightly higher
        intensity to test robustness. This is the 'adaptive escalation' loop.
        """
        for attack_type, det_rate in detection_rate_by_type.items():
            persona = self.personas[attack_type]
            persona.history.append(det_rate)
            persona.rounds_played += 1
            step = 0.12
            if det_rate > 0.6:
                # getting caught too often -> become stealthier, reduce obvious intensity
                persona.stealth_bias = float(np.clip(persona.stealth_bias + step, 0.05, 0.95))
                persona.intensity = float(np.clip(persona.intensity - step * 0.5, 0.05, 0.95))
            elif det_rate < 0.25:
                # evading well -> escalate intensity to probe how far it can push
                persona.intensity = float(np.clip(persona.intensity + step, 0.05, 0.95))
                persona.stealth_bias = float(np.clip(persona.stealth_bias - step * 0.3, 0.05, 0.95))
            else:
                # mixed results -> small random exploration (bandit-style jitter)
                persona.intensity = float(np.clip(persona.intensity + self.rng.normal(0, 0.05), 0.05, 0.95))
                persona.stealth_bias = float(np.clip(persona.stealth_bias + self.rng.normal(0, 0.05), 0.05, 0.95))

    def persona_state(self) -> pd.DataFrame:
        return pd.DataFrame([
            {"attack_type": p.attack_type, "intensity": p.intensity, "stealth_bias": p.stealth_bias,
             "rounds_played": p.rounds_played, "last_detection_rate": (p.history[-1] if p.history else None)}
            for p in self.personas.values()
        ])


if __name__ == "__main__":
    df = pd.read_parquet("/home/claude/mastercard-ai-defense-lab/outputs/synthetic_transactions.parquet")
    legit = df[df["fraud_label"] == 0]
    agent = RedTeamAgent()
    batch = agent.generate_attack_batch(legit, n_per_type=200)
    print(batch.shape)
    print(batch["attack_type"].value_counts())
    print(batch[["attack_type", "amount", "original_amount", "geo_distance_km", "txn_count_last_1h"]].head(10))
