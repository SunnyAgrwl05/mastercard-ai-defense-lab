# 🛡️ Mastercard AI Defense Lab

### Red Team × Blue Team — AI-Powered Payment Fraud Defense

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Online-success?style=for-the-badge)](https://mastercard-ai-defense-lab.onrender.com/)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github)](https://github.com/SunnyAgrwl05/mastercard-ai-defense-lab)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-Model-EB6A0A)
![scikit--learn](https://img.shields.io/badge/scikit--learn-ML-F7931E?logo=scikitlearn&logoColor=white)
![SHAP](https://img.shields.io/badge/SHAP-Explainability-6A4C93)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker&logoColor=white)

**🚀 Live Demo:** https://mastercard-ai-defense-lab.onrender.com/
**💻 Repository:** https://github.com/SunnyAgrwl05/mastercard-ai-defense-lab

---

## Live Defense Command Center

The deployed frontend is an interactive, browser-based payment-security dashboard — the **Defense Command Center**. It lets anyone, without setup, explore the full closed-loop system:

- Real-time transaction risk scoring
- Adversarial attack simulation against the live model
- Model performance and evaluation metrics
- Red-Team vs Blue-Team results, before and after adversarial retraining
- Live API health and system status

**Open it here:** https://mastercard-ai-defense-lab.onrender.com/

---

## Aim / Mission

Most fraud-detection projects train a classifier once and stop. **Mastercard AI Defense Lab** treats fraud defense as an ongoing contest between an attacker and a defender.

The mission is to build a **closed-loop Red Team × Blue Team system** where:

1. A **Blue Team** model learns to detect fraudulent payments.
2. A **Red Team** engine actively searches for transaction patterns the Blue Team fails to catch.
3. Every attack the Blue Team misses is fed back into training.
4. The Blue Team is retrained and re-tested against fresh, unseen attacks.

The goal is not a single accuracy number — it is a system that keeps testing and improving itself.

---

## Problem

Conventional, static fraud-detection models are trained once on historical data and then deployed unchanged. This works reasonably well against known fraud patterns, but it struggles against attackers who:

- Deliberately shape transactions to stay just under known detection thresholds
- Spread suspicious activity across time, merchants, or devices so no single signal stands out
- Mimic a genuine customer's historical spending behavior
- Adapt as soon as one strategy stops working

A model that is only ever evaluated on the fraud patterns it was trained on will consistently overestimate its own real-world resilience.

---

## Solution

The system is built as a continuous feedback loop rather than a single training pass:

```text
Synthetic Transaction Generation
              ↓
        Blue-Team Detection
              ↓
       Red-Team Attack Simulation
              ↓
      Missed-Attack Identification
              ↓
        Adversarial Retraining
              ↓
         Improved Blue-Team Model
              ↓
             Repeat
```

Each cycle produces a Blue-Team model that has been explicitly stress-tested against attacks generated to exploit its own weaknesses.

---

## Why This Project Is Different

**Traditional fraud detection asks:**
> "Can the model detect fraud in this dataset?"

**AI Defense Lab asks:**
> "Can the model survive an attacker that is actively searching for its blind spots — and can it get better every time it fails?"

| | Traditional Detection | AI Defense Lab |
|---|---|---|
| Evaluation | Static historical test set | Adversarially generated attacks |
| Model lifecycle | Train once, deploy | Continuous generate → attack → detect → retrain loop |
| Attack awareness | Reactive (after real fraud occurs) | Proactive (simulated before deployment) |
| Reporting | Single accuracy/F1 number | Per-attack-family detection rates, before vs after |

---

## Blue Team — Fraud Detection Layer

The Blue Team is the machine-learning defense layer. It scores each transaction using features such as:

- Transaction amount
- Customer's historical spending baseline
- Merchant category and merchant risk score
- Device type
- Geographic distance from home/usual location
- Transaction frequency (velocity) in the last 24 hours
- Recent failed-transaction count
- Hour of day / time-based patterns

Multiple candidate models are trained and compared:

- **XGBoost**
- **Random Forest**
- **Isolation Forest**

The best-performing model on the validation set is selected as the production Blue-Team detector. Each prediction returns a fraud probability, a 0–100 risk score, a risk bucket, and a plain-English narrative describing the main contributing signals.

---

## Red Team — Adversarial Attack Engine

The Red Team generates synthetic adversarial transactions across **seven attack families**, each designed to test a different weakness in the detector:

| Attack Family | What It Tests |
|---|---|
| `amount_manipulation` | Whether the detector relies too heavily on fixed amount thresholds |
| `velocity_attack` | Whether rapid bursts of transactions across merchants/devices slip past frequency checks |
| `merchant_switching` | Whether spreading spend across many merchant categories avoids single-signal spikes |
| `geo_evasion` | Whether keeping location changes within a plausible commute radius avoids geographic flags |
| `account_takeover` | Whether sudden combined changes in device, location, amount, and velocity are caught |
| `low_and_slow` | Whether many small transactions under the customer's usual pattern go undetected |
| `behavioral_mimicry` | Whether fraud crafted to resemble the victim's own historical spending behavior is caught |

Each family accepts an **intensity** parameter, allowing attacks to be generated on a spectrum from subtle to aggressive.

---

## Closed-Loop Adversarial Learning

The core mechanism of the project is the adversarial training loop:

**Round 1 — Baseline evaluation**
```text
Generate adversarial transactions
              ↓
    Blue Team scores each attack
              ↓
     Record which attacks are missed
```

**Round 2 — Adversarial retraining**
```text
Missed attacks
      ↓
Added to the training dataset
      ↓
Blue-Team model is retrained
```

**Round 3 — Resilience test**
```text
Generate fresh, unseen attacks
              ↓
    Evaluate the retrained detector
              ↓
   Compare detection rate: before vs after
```

This loop can be repeated multiple times, and each pass is intended to close a specific gap that the previous round exposed.

---

## Results

All results below come from the project's synthetic research dataset and evaluation run.

**Dataset**
- 160,265 synthetic transactions
- 900 synthetic accounts
- 80 days of simulated activity
- 2.00% synthetic fraud prevalence

**Blue-Team Baseline (XGBoost)**

| Metric | Result |
|---|---|
| Accuracy | 97.7% |
| Precision | 47.1% |
| Recall | 94.7% |
| F1 Score | 62.9% |
| ROC-AUC | 0.995 |
| PR-AUC | 0.917 |

> Accuracy alone is not a meaningful metric on an imbalanced fraud dataset — precision, recall, F1, and PR-AUC are the metrics that matter here.

**Red-Team Attack Detection**

| Stage | Overall Detection Rate |
|---|---|
| Before adversarial training | 11.7% |
| After 2 adversarial-training rounds | 62.0% |

> These are synthetic research/hackathon prototype results. They are **not** Mastercard production performance figures and should not be interpreted as such.

---

## Before vs After — Detection Comparison

| Metric | Before Adversarial Training | After Adversarial Training |
|---|---|---|
| Overall attack detection rate | 11.7% | 62.0% |
| Average risk score on attacks | 13.1 / 100 | 63.8 / 100 |
| Adversarial examples added to training | — | 1,353 |

---

## Attack-Family Detection Rates

**Before adversarial training**

| Attack Family | Detection Rate |
|---|---|
| geo_evasion | 0.7% |
| velocity_attack | 1.3% |
| low_and_slow | 2.0% |
| amount_manipulation | 4.7% |
| merchant_switching | 8.0% |
| behavioral_mimicry | 8.0% |
| account_takeover | 57.3% |

**After 2 adversarial-training rounds**

| Attack Family | Detection Rate |
|---|---|
| geo_evasion | 5.3% |
| behavioral_mimicry | 39.3% |
| amount_manipulation | 42.7% |
| merchant_switching | 49.3% |
| low_and_slow | 98.0% |
| account_takeover | 99.3% |
| velocity_attack | 100.0% |

`geo_evasion` remains the hardest attack family to detect with the current feature set — a known, honestly reported limitation rather than an unexplained gap.

---

## Honest Trade-Off

Adversarial retraining substantially improved attack coverage, but it also shifted the decision boundary on clean (legitimate) transactions:

| Metric | Before Retraining | After Retraining |
|---|---|---|
| Precision | 0.471 | 0.315 |
| Recall | 0.947 | 0.956 |
| F1 Score | 0.629 | 0.474 |
| ROC-AUC | 0.995 | 0.990 |
| PR-AUC | 0.917 | 0.906 |

Improving adversarial coverage increased false-positive pressure on legitimate transactions. A production deployment would need to manage this trade-off using:

- Risk-band-specific threshold calibration
- Cost-sensitive learning
- Human-in-the-loop review for borderline cases
- Continuous monitoring of precision/recall drift

---

## Explainable AI

Each risk score is accompanied by an explanation rather than a bare probability:

- SHAP-based feature importance for the trained model
- Ranked list of the top contributing risk signals per transaction
- A plain-English risk narrative summarizing why a transaction was scored the way it was

**Example**

```text
Risk Score: 87.4 / 100
Risk Level: High

Main Contributing Signals:
- Unusual transaction amount
- High transaction velocity
- Geographic distance from home location
- Recent failed-transaction activity
```

---

## Live Frontend — Defense Command Center

The frontend (`web/index.html`) is a self-contained interactive dashboard that talks directly to the FastAPI backend. It includes:

- **Dashboard** — model performance, fraud recall, ROC-AUC/PR-AUC, closed-loop detection improvement, and system health
- **Transaction Analyzer** — submit a transaction and view its live fraud probability, risk score, and explanation
- **Attack Simulator** — choose an attack family and intensity, generate an adversarial transaction, and see whether the detector catches it
- **Red-Team Arsenal** — an overview of all seven attack families and their evasion characteristics
- **Model Evaluation** — charts for attack detection by type, closed-loop before/after impact, ROC curve, and top risk signals
- **API Console / System Health** — live backend status for the FastAPI service and loaded model

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Returns API and model-load status |
| `/predict` | POST | Scores a single transaction and returns fraud probability, risk score, and explanation |
| `/simulate-attack` | POST | Applies a chosen Red-Team attack to a base transaction and scores the result |
| `/red-team` | POST | Runs a batch of Red-Team attacks and returns aggregate detection results |
| `/metrics` | GET | Returns pre-computed evaluation metrics for the dashboard |

**Interactive API documentation** (when running locally):