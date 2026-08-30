"""
preprocessing.py
=================
Feature engineering, encoding, and leakage-safe train/val/test splitting for
the synthetic payment dataset.

Leakage-avoidance rules followed here:
  1. Split is done by TIME (chronological) per the global timeline, not randomly,
     so the model is always validated/tested on transactions that happened
     *after* those it trained on -- this mirrors production fraud-detection
     deployment and prevents "future leaking into past".
  2. Scalers / encoders are `fit` ONLY on the training partition and then
     `transform`-applied to validation/test -- never fit on the full dataset.
  3. `fraud_label` and any post-hoc labels are excluded from the feature matrix.
  4. Row identifiers (transaction_id, account_id, timestamp) are kept aside as
     metadata, not fed to the model as raw features (account_id is high-
     cardinality and would leak identity rather than behaviour).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from dataclasses import dataclass


CATEGORICAL_COLS = ["merchant_category", "device_type", "payment_method"]
NUMERIC_COLS = [
    "amount", "merchant_risk_score", "geo_distance_km", "account_age_days",
    "failed_txn_count_recent", "seconds_since_prev_txn", "txn_count_last_1h",
    "txn_count_last_24h", "amount_avg_last_5", "amount_deviation_ratio",
    "is_new_device_hint", "hour_of_day", "day_of_week", "is_weekend",
]
LABEL_COL = "fraud_label"
META_COLS = ["transaction_id", "account_id", "timestamp"]


@dataclass
class SplitData:
    X_train: pd.DataFrame
    X_val: pd.DataFrame
    X_test: pd.DataFrame
    y_train: pd.Series
    y_val: pd.Series
    y_test: pd.Series
    meta_train: pd.DataFrame
    meta_val: pd.DataFrame
    meta_test: pd.DataFrame
    scaler: StandardScaler
    encoder: OneHotEncoder
    feature_names: list


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add a few extra engineered ratios on top of data_generator's raw output."""
    df = df.copy()
    df["velocity_score"] = (df["txn_count_last_1h"] * 3 + df["txn_count_last_24h"]).astype(float)
    df["amount_log"] = np.log1p(df["amount"])
    df["is_high_risk_merchant"] = (df["merchant_risk_score"] > 0.20).astype(int)
    df["is_far_from_home"] = (df["geo_distance_km"] > 100).astype(int)
    df["rapid_repeat_txn"] = (df["seconds_since_prev_txn"] < 60).astype(int)
    return df


def chronological_split(df: pd.DataFrame, train_frac=0.6, val_frac=0.2):
    """Split by global timestamp order: earliest `train_frac` -> train, next
    `val_frac` -> val, remainder -> test. Prevents future-to-past leakage."""
    df = df.sort_values("timestamp").reset_index(drop=True)
    n = len(df)
    i_train = int(n * train_frac)
    i_val = int(n * (train_frac + val_frac))
    return df.iloc[:i_train].copy(), df.iloc[i_train:i_val].copy(), df.iloc[i_val:].copy()


def fit_transform_splits(df: pd.DataFrame) -> SplitData:
    df = engineer_features(df)
    numeric_cols = NUMERIC_COLS + ["velocity_score", "amount_log", "is_high_risk_merchant",
                                    "is_far_from_home", "rapid_repeat_txn"]

    train_df, val_df, test_df = chronological_split(df)

    encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    encoder.fit(train_df[CATEGORICAL_COLS])

    scaler = StandardScaler()
    scaler.fit(train_df[numeric_cols])

    def build(part_df: pd.DataFrame):
        num = scaler.transform(part_df[numeric_cols])
        cat = encoder.transform(part_df[CATEGORICAL_COLS])
        cat_names = encoder.get_feature_names_out(CATEGORICAL_COLS)
        X = pd.DataFrame(np.hstack([num, cat]), columns=numeric_cols + list(cat_names), index=part_df.index)
        y = part_df[LABEL_COL].reset_index(drop=True)
        X = X.reset_index(drop=True)
        meta = part_df[META_COLS].reset_index(drop=True)
        return X, y, meta

    X_train, y_train, meta_train = build(train_df)
    X_val, y_val, meta_val = build(val_df)
    X_test, y_test, meta_test = build(test_df)

    feature_names = list(X_train.columns)

    return SplitData(
        X_train=X_train, X_val=X_val, X_test=X_test,
        y_train=y_train, y_val=y_val, y_test=y_test,
        meta_train=meta_train, meta_val=meta_val, meta_test=meta_test,
        scaler=scaler, encoder=encoder, feature_names=feature_names,
    )


def transform_new(rows_df: pd.DataFrame, scaler: StandardScaler, encoder: OneHotEncoder, feature_names: list) -> pd.DataFrame:
    """Apply an already-fit scaler/encoder to new (e.g. Red-Team generated) rows."""
    df = engineer_features(rows_df)
    numeric_cols = NUMERIC_COLS + ["velocity_score", "amount_log", "is_high_risk_merchant",
                                    "is_far_from_home", "rapid_repeat_txn"]
    num = scaler.transform(df[numeric_cols])
    cat = encoder.transform(df[CATEGORICAL_COLS])
    cat_names = encoder.get_feature_names_out(CATEGORICAL_COLS)
    X = pd.DataFrame(np.hstack([num, cat]), columns=numeric_cols + list(cat_names), index=df.index)
    return X[feature_names]


if __name__ == "__main__":
    df = pd.read_parquet("/home/claude/mastercard-ai-defense-lab/outputs/synthetic_transactions.parquet")
    split = fit_transform_splits(df)
    print("train/val/test:", split.X_train.shape, split.X_val.shape, split.X_test.shape)
    print("fraud rate train/val/test:", split.y_train.mean(), split.y_val.mean(), split.y_test.mean())
