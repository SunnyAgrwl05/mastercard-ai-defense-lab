"""
api/main.py
===========
FastAPI backend for the AI Defense Lab for Payment Security prototype.

Endpoints:
  GET  /health              -> service + model status
  POST /predict              -> risk-score a transaction
  POST /simulate-attack       -> Red-Team: turn a transaction into an attack
  POST /red-team              -> Red-Team: generate + immediately score a batch attack, per type
  GET  /metrics                -> the real, pre-computed closed-loop metrics (for the dashboard)
  GET  /                        -> serves the web prototype (static/index.html)

Loads the ALREADY-TRAINED closed-loop detector (fraud_detector_after_closed_loop.pkl).
No paid/external API keys are required anywhere in this service.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Optional

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "src"))

from preprocessing import transform_new  # noqa: E402
from blue_team import BlueTeamDetector, risk_band  # noqa: E402
from red_team import RedTeamAgent, ATTACK_TYPES  # noqa: E402
from explainability import Explainer  # noqa: E402

app = FastAPI(title="Mastercard AI Defense Lab — Payment Fraud Red/Blue Team API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_state = {"split": None, "detector": None, "explainer": None, "agent": None}


def _load():
    if _state["detector"] is None:
        model_path = os.path.join(BASE, "models", "fraud_detector_after_closed_loop.pkl")
        if not os.path.exists(model_path):
            model_path = os.path.join(BASE, "models", "fraud_detector.pkl")
        _state["split"] = joblib.load(os.path.join(BASE, "models", "split_data.pkl"))
        _state["detector"] = BlueTeamDetector.load(model_path)
        _state["explainer"] = Explainer(_state["detector"], background=_state["split"].X_train)
        _state["agent"] = RedTeamAgent(rng_seed=int.from_bytes(os.urandom(2), "big"))
    return _state


class Transaction(BaseModel):
    amount: float = Field(..., example=250.0)
    merchant_category: str = Field(..., example="electronics")
    merchant_risk_score: float = Field(0.1, example=0.1)
    device_type: str = Field(..., example="mobile_app")
    payment_method: str = Field(..., example="chip")
    geo_distance_km: float = Field(5.0, example=5.0)
    account_age_days: int = Field(400, example=400)
    failed_txn_count_recent: int = Field(0, example=0)
    seconds_since_prev_txn: float = Field(3600.0, example=3600.0)
    txn_count_last_1h: int = Field(0, example=0)
    txn_count_last_24h: int = Field(1, example=1)
    amount_avg_last_5: float = Field(200.0, example=200.0)
    amount_deviation_ratio: float = Field(1.0, example=1.0)
    is_new_device_hint: int = Field(0, example=0)
    hour_of_day: int = Field(14, example=14)
    day_of_week: int = Field(2, example=2)
    is_weekend: int = Field(0, example=0)


class AttackRequest(BaseModel):
    transaction: Transaction
    attack_type: str = Field(..., example="amount_manipulation")


class RedTeamBatchRequest(BaseModel):
    n_per_type: int = Field(30, ge=1, le=300)


@app.get("/health")
def health():
    st = _load()
    return {
        "status": "ok",
        "model_loaded": st["detector"] is not None,
        "model_used": st["detector"].best_model_name,
        "attack_types": ATTACK_TYPES,
        "note": "Synthetic-data research prototype. Not connected to any real Mastercard system.",
    }


@app.post("/predict")
def predict(txn: Transaction):
    st = _load()
    row = pd.DataFrame([txn.dict()])
    X = transform_new(row, st["split"].scaler, st["split"].encoder, st["split"].feature_names)
    explanation = st["explainer"].explain_row(X)
    explanation["risk_band"] = risk_band(explanation["risk_score"])
    return explanation


@app.post("/simulate-attack")
def simulate_attack_endpoint(req: AttackRequest):
    st = _load()
    if req.attack_type not in ATTACK_TYPES:
        raise HTTPException(400, f"attack_type must be one of {ATTACK_TYPES}")
    attacked = st["agent"].craft_attack(req.transaction.dict(), req.attack_type)
    row = pd.DataFrame([attacked])
    feature_cols = [c for c in row.columns if c in Transaction.__fields__]
    X = transform_new(row[feature_cols], st["split"].scaler, st["split"].encoder, st["split"].feature_names)
    explanation = st["explainer"].explain_row(X)
    explanation["risk_band"] = risk_band(explanation["risk_score"])
    explanation["attacked_transaction"] = {k: attacked[k] for k in feature_cols}
    explanation["attack_type"] = req.attack_type
    return explanation


@app.post("/red-team")
def red_team_batch(req: RedTeamBatchRequest):
    """Generate a synthetic attack batch across all 7 families and score them
    immediately with the current detector — returns per-family detection stats."""
    st = _load()
    base_df = pd.read_parquet(os.path.join(BASE, "outputs", "synthetic_transactions.parquet"))
    legit = base_df[base_df["fraud_label"] == 0]
    batch = st["agent"].generate_attack_batch(legit, n_per_type=req.n_per_type)
    X = transform_new(batch, st["split"].scaler, st["split"].encoder, st["split"].feature_names)
    proba = st["detector"].predict_proba(X)
    batch["risk_score"] = (proba * 100).round(1)
    batch["detected"] = (proba >= 0.5).astype(int)
    summary = batch.groupby("attack_type").agg(
        number_generated=("attack_type", "count"),
        number_detected=("detected", "sum"),
        avg_risk_score=("risk_score", "mean"),
    ).reset_index()
    summary["detection_rate"] = (summary["number_detected"] / summary["number_generated"]).round(4)
    summary["avg_risk_score"] = summary["avg_risk_score"].round(2)
    return {"summary": summary.to_dict(orient="records"), "n_total": int(len(batch))}


@app.get("/metrics")
def metrics():
    """Serve the real, previously-computed closed-loop evaluation results for
    the dashboard (not re-computed live, so the dashboard loads instantly)."""
    metrics_dir = os.path.join(BASE, "outputs", "metrics")
    out = {}
    summary_path = os.path.join(metrics_dir, "closed_loop_summary.json")
    if os.path.exists(summary_path):
        with open(summary_path) as f:
            out["closed_loop_summary"] = json.load(f)
    for name, fname in [
        ("round1_before", "round1_before_attack_summary.csv"),
        ("final_after", "final_after_attack_summary.csv"),
        ("persona_state", "red_team_persona_final_state.csv"),
    ]:
        p = os.path.join(metrics_dir, fname)
        if os.path.exists(p):
            out[name] = pd.read_csv(p).to_dict(orient="records")
    return out


# ---- serve the web prototype ----
web_dir = os.path.join(BASE, "web")
figures_dir = os.path.join(BASE, "outputs", "figures")
if os.path.isdir(figures_dir):
    app.mount("/figures", StaticFiles(directory=figures_dir), name="figures")
if os.path.isdir(web_dir):
    app.mount("/static", StaticFiles(directory=web_dir), name="static")

    @app.get("/")
    def index():
        return FileResponse(os.path.join(web_dir, "index.html"))
