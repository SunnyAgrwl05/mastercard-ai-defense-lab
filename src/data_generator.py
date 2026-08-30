"""
data_generator.py
==================
Generates a SYNTHETIC payment-transaction dataset for the Mastercard Innovation
Challenge 2026 (AI Defense Lab for Payment Security).

IMPORTANT: This data is 100% synthetic. It does NOT contain, derive from, or
represent any real Mastercard transaction, cardholder, or merchant data. It is
built from statistical distributions chosen to resemble publicly documented
characteristics of retail card-payment behaviour (e.g. log-normal amounts,
diurnal transaction cycles, Zipfian merchant popularity) purely for the
purpose of building and stress-testing a fraud-detection research prototype.

Reproducibility: every random draw is derived from a single seed (default 42)
via a `numpy.random.Generator`, so re-running this script produces bit-identical
output.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass
from datetime import datetime, timedelta


MERCHANT_CATEGORIES = [
    "grocery", "electronics", "travel", "restaurant", "fuel",
    "online_retail", "utilities", "entertainment", "healthcare",
    "jewelry", "gambling", "crypto_exchange", "money_transfer", "atm_withdrawal",
]

# Rough prior "riskiness" per category (0-1). Used only to bias fraud
# likelihood in the synthetic generator -- not a claim about real-world risk.
MERCHANT_RISK_PRIOR = {
    "grocery": 0.02, "electronics": 0.12, "travel": 0.10, "restaurant": 0.03,
    "fuel": 0.03, "online_retail": 0.10, "utilities": 0.01, "entertainment": 0.05,
    "healthcare": 0.02, "jewelry": 0.22, "gambling": 0.30, "crypto_exchange": 0.35,
    "money_transfer": 0.28, "atm_withdrawal": 0.15,
}

DEVICE_TYPES = ["mobile_app", "web_chrome", "web_safari", "pos_chip", "pos_contactless", "atm"]
PAYMENT_METHODS = ["chip", "contactless", "online_card_not_present", "magstripe", "wallet"]

N_ACCOUNTS_DEFAULT = 900
N_TXN_DEFAULT = 260_000  # kept for reference; actual count is driven by per-account rates x days
FRAUD_RATE_DEFAULT = 0.02  # ~2% base fraud rate (realistic order of magnitude)


@dataclass
class Account:
    account_id: str
    home_lat: float
    home_lon: float
    account_age_days: int
    avg_amount: float
    std_amount: float
    favourite_categories: list
    favourite_device: str
    monthly_txn_rate: float  # expected txns/day


def _sample_accounts(rng: np.random.Generator, n_accounts: int) -> list[Account]:
    accounts = []
    # Home locations spread across a handful of city hubs (lat, lon) + jitter,
    # so "geographic distance" features have realistic clustering.
    hubs = [(28.61, 77.20), (19.07, 72.87), (12.97, 77.59), (22.57, 88.36),
            (13.08, 80.27), (17.38, 78.48), (23.02, 72.57), (26.85, 80.94)]
    for i in range(n_accounts):
        hub = hubs[rng.integers(0, len(hubs))]
        home_lat = hub[0] + rng.normal(0, 0.35)
        home_lon = hub[1] + rng.normal(0, 0.35)
        age = int(rng.exponential(650)) + 30
        avg_amount = float(np.clip(rng.lognormal(mean=6.2, sigma=0.9), 50, 20000))
        std_amount = avg_amount * rng.uniform(0.2, 0.6)
        fav_cats = list(rng.choice(MERCHANT_CATEGORIES, size=rng.integers(2, 5), replace=False))
        fav_device = DEVICE_TYPES[rng.integers(0, len(DEVICE_TYPES))]
        monthly_rate = float(np.clip(rng.gamma(shape=2.0, scale=1.1), 0.05, 8.0))
        accounts.append(Account(
            account_id=f"ACC{i:06d}", home_lat=home_lat, home_lon=home_lon,
            account_age_days=age, avg_amount=avg_amount, std_amount=std_amount,
            favourite_categories=fav_cats, favourite_device=fav_device,
            monthly_txn_rate=monthly_rate,
        ))
    return accounts


def _haversine(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dl = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def generate_transactions(
    n_accounts: int = N_ACCOUNTS_DEFAULT,
    n_transactions: int = N_TXN_DEFAULT,
    fraud_rate: float = FRAUD_RATE_DEFAULT,
    seed: int = 42,
    start: datetime = datetime(2026, 1, 1),
    days: int = 80,
) -> pd.DataFrame:
    """Generate a synthetic legitimate+fraud transaction dataset.

    Returns a DataFrame with one row per transaction and a `fraud_label` column
    (1 = fraud, 0 = legitimate). Fraud transactions here are "organic" fraud
    patterns baked into the base dataset (stolen-card one-off spikes, ATO-like
    bursts); the dedicated Red-Team module (red_team.py) additionally crafts
    *adversarial* attacks against a trained detector on top of this data.
    """
    rng = np.random.default_rng(seed)
    accounts = _sample_accounts(rng, n_accounts)

    rows = []
    txn_counter = 0
    # Approximate how many "events" (transactions) to spread across accounts x days
    for acc in accounts:
        expected_txns = max(1, int(acc.monthly_txn_rate * days * rng.uniform(0.7, 1.3)))
        # timestamps: diurnal pattern via a mixture of normals around 10am/1pm/7pm
        day_offsets = rng.integers(0, days, size=expected_txns)
        hour_modes = rng.choice([10, 13, 19], size=expected_txns, p=[0.35, 0.30, 0.35])
        hours = np.clip(rng.normal(hour_modes, 2.2), 0, 23.9)

        prev_device = acc.favourite_device
        prev_lat, prev_lon = acc.home_lat, acc.home_lon
        failed_count = 0

        order = np.argsort(day_offsets + hours / 24.0)
        for k in order:
            txn_counter += 1
            ts = start + timedelta(days=float(day_offsets[k]), hours=float(hours[k]))

            is_fraud = rng.random() < fraud_rate
            if is_fraud:
                # Organic fraud archetypes baked into base data (distinct from
                # Red-Team's adversarial-attack generation used later).
                archetype = rng.choice(["stolen_card_spike", "ato_burst", "card_testing"])
                if archetype == "stolen_card_spike":
                    amount = float(np.clip(rng.lognormal(mean=np.log(acc.avg_amount * 4), sigma=0.6), 100, 150000))
                    category = rng.choice(["electronics", "jewelry", "crypto_exchange", "gambling", "online_retail"])
                    device = rng.choice([d for d in DEVICE_TYPES if d != acc.favourite_device])
                    dist_km = float(np.clip(rng.exponential(600), 5, 15000))
                elif archetype == "ato_burst":
                    amount = float(np.clip(rng.lognormal(mean=np.log(max(acc.avg_amount, 50) * 2.2), sigma=0.5), 50, 80000))
                    category = rng.choice(["money_transfer", "crypto_exchange", "electronics"])
                    device = rng.choice(DEVICE_TYPES)
                    dist_km = float(np.clip(rng.exponential(300), 1, 9000))
                else:  # card_testing: many tiny txns
                    amount = float(np.clip(rng.normal(2.5, 1.2), 0.5, 15))
                    category = rng.choice(["online_retail", "utilities", "entertainment"])
                    device = "web_chrome"
                    dist_km = float(np.clip(rng.exponential(150), 0, 5000))
                failed_count = int(np.clip(failed_count + rng.integers(0, 3), 0, 20))
            else:
                category = rng.choice(acc.favourite_categories) if rng.random() < 0.75 else rng.choice(MERCHANT_CATEGORIES)
                amount = float(np.clip(rng.lognormal(mean=np.log(max(acc.avg_amount, 10)), sigma=0.55), 1, 50000))
                device = acc.favourite_device if rng.random() < 0.85 else rng.choice(DEVICE_TYPES)
                dist_km = float(np.clip(rng.exponential(8) if rng.random() < 0.9 else rng.exponential(200), 0, 12000))
                failed_count = int(np.clip(failed_count + (1 if rng.random() < 0.03 else -1), 0, 20))

            lat = acc.home_lat + rng.normal(0, 0.05) if dist_km < 20 else acc.home_lat + rng.normal(0, 3)
            lon = acc.home_lon + rng.normal(0, 0.05) if dist_km < 20 else acc.home_lon + rng.normal(0, 3)
            actual_dist = _haversine(acc.home_lat, acc.home_lon, lat, lon)

            payment_method = rng.choice(PAYMENT_METHODS, p=[0.30, 0.28, 0.22, 0.08, 0.12])
            merchant_risk = float(np.clip(MERCHANT_RISK_PRIOR[category] + rng.normal(0, 0.03), 0.005, 0.9))

            rows.append({
                "transaction_id": f"TXN{txn_counter:08d}",
                "account_id": acc.account_id,
                "timestamp": ts,
                "amount": round(amount, 2),
                "merchant_category": category,
                "merchant_risk_score": round(merchant_risk, 4),
                "device_type": device,
                "payment_method": payment_method,
                "geo_distance_km": round(float(actual_dist), 2),
                "account_age_days": acc.account_age_days,
                "failed_txn_count_recent": failed_count,
                "fraud_label": int(is_fraud),
            })
            prev_device, prev_lat, prev_lon = device, lat, lon

    df = pd.DataFrame(rows)
    df = df.sort_values("timestamp").reset_index(drop=True)

    # ---- velocity / frequency features computed causally (no leakage) ----
    df = df.sort_values(["account_id", "timestamp"]).reset_index(drop=True)
    df["prev_txn_time"] = df.groupby("account_id")["timestamp"].shift(1)
    df["seconds_since_prev_txn"] = (df["timestamp"] - df["prev_txn_time"]).dt.total_seconds()
    df["seconds_since_prev_txn"] = df["seconds_since_prev_txn"].fillna(df["seconds_since_prev_txn"].median())

    df["txn_count_last_1h"] = 0
    df["txn_count_last_24h"] = 0
    df["amount_avg_last_5"] = np.nan
    for acc_id, g in df.groupby("account_id", sort=False):
        idx = g.index
        times = g["timestamp"].values.astype("datetime64[s]").astype(np.int64)
        amounts = g["amount"].values
        n = len(g)
        c1h = np.zeros(n, dtype=int)
        c24h = np.zeros(n, dtype=int)
        avg5 = np.full(n, np.nan)
        j1, j24 = 0, 0
        for i in range(n):
            while times[i] - times[j1] > 3600:
                j1 += 1
            while times[i] - times[j24] > 86400:
                j24 += 1
            c1h[i] = i - j1
            c24h[i] = i - j24
            avg5[i] = amounts[max(0, i - 5):i].mean() if i > 0 else amounts[i]
        df.loc[idx, "txn_count_last_1h"] = c1h
        df.loc[idx, "txn_count_last_24h"] = c24h
        df.loc[idx, "amount_avg_last_5"] = avg5

    df["amount_avg_last_5"] = df["amount_avg_last_5"].fillna(df["amount"])
    df["amount_deviation_ratio"] = (df["amount"] / df["amount_avg_last_5"].replace(0, np.nan)).fillna(1.0)
    df["is_new_device_hint"] = (rng.random(len(df)) < 0.08).astype(int)  # weak noisy signal, not leakage-free proxy for label
    df["hour_of_day"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

    df = df.drop(columns=["prev_txn_time"])
    return df


if __name__ == "__main__":
    df = generate_transactions()
    print(df.shape)
    print(df["fraud_label"].value_counts(normalize=True))
    df.to_parquet("/home/claude/mastercard-ai-defense-lab/outputs/synthetic_transactions.parquet", index=False)
    print("saved.")
