# 🛡️ Mastercard AI Defense Lab

### Red Team × Blue Team · AI-Powered Payment Fraud Defense

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

The deployed frontend is an interactive, browser-based payment-security dashboard — the **Defense Command Center**. It lets anyone, without any local setup, explore the full closed-loop system:

- Real-time transaction risk scoring
- Adversarial attack simulation against the live model
- Model performance and evaluation metrics
- Red-Team vs Blue-Team results, before and after adversarial retraining
- Live API health and system status

**Open it here:** https://mastercard-ai-defense-lab.onrender.com/

---

## 🎯 Aim of the Project

The goal of **Mastercard AI Defense Lab** is to demonstrate a closed-loop payment-fraud defense system in which a detector is continuously stress-tested and improved by its own simulated attacker:

```text
Synthetic Transactions
        ↓
   Blue-Team Detection
        ↓
   Red-Team Attacks
        ↓
  Missed-Attack Discovery
        ↓
 Adversarial Retraining
        ↓
  Improved Blue Team
        ↓
      Repeat
```

Rather than training a fraud classifier once and reporting a single accuracy number, the system treats defense as an ongoing loop: generate synthetic data, detect fraud, attack the detector, learn from what it misses, and retrain.

---

## Why This Is Different From a Traditional Fraud Detector

**Traditional fraud detection asks:**
> "Can the model detect fraud in this dataset?"

**AI Defense Lab asks:**
> "Can the model survive an attacker that is actively searching for its weaknesses — and does it get measurably better after learning from what it missed?"

| | Traditional Detection | AI Defense Lab |
|---|---|---|
| Evaluation | Static historical test set | Adversarially generated attacks |
| Model lifecycle | Train once, deploy | Continuous generate → attack → detect → retrain loop |
| Attack awareness | Reactive, after fraud occurs | Proactive, simulated before deployment |
| Reporting | Single accuracy/F1 number | Per-attack-family detection rates, before vs after retraining |

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

Multiple candidate models are trained and compared for model selection:

- **XGBoost**
- **Random Forest**
- **Isolation Forest**

The best-performing model on the validation set is selected as the production Blue-Team detector. Each prediction returns a fraud probability, a 0–100 risk score, a risk bucket, and a plain-English narrative describing the main contributing signals (explainability).

---

## Red Team — Adversarial Attack Engine

The Red Team generates synthetic adversarial transactions across the **seven attack families implemented in the repository**, each targeting a different potential weakness in the detector:

| Attack Family | What It Tests |
|---|---|
| `amount_manipulation` | Whether the detector relies too heavily on fixed amount thresholds |
| `velocity_attack` | Whether rapid bursts of transactions across merchants/devices slip past frequency checks |
| `merchant_switching` | Whether spreading spend across many merchant categories avoids single-signal spikes |
| `geo_evasion` | Whether keeping location changes within a plausible commute radius avoids geographic flags |
| `account_takeover` | Whether sudden combined changes in device, location, amount, and velocity are caught |
| `low_and_slow` | Whether many small transactions under the customer's usual pattern go undetected |
| `behavioral_mimicry` | Whether fraud crafted to resemble the victim's own historical spending behavior is caught |

Each family accepts an **intensity** parameter, so attacks can be generated across a spectrum from subtle to aggressive. A generated attack is passed straight back into the Blue-Team detector, which scores it exactly like any other transaction — this is the interaction point between the two teams.

---

## Closed-Loop Adversarial Training

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

This loop can be repeated across multiple rounds, with each pass intended to close a specific gap the previous round exposed.

---

## Results

All results below come from the project's synthetic research dataset and evaluation run. **These are synthetic research/hackathon prototype results and are NOT Mastercard production performance figures.**

**Dataset**
- 160,265 synthetic transactions
- 900 synthetic accounts
- 80 days of simulated activity
- 2.00% synthetic fraud prevalence

**Blue-Team Baseline (XGBoost)**

| Metric | Result |
|---|---|
| Accuracy | 0.977 |
| Precision | 0.471 |
| Recall | 0.947 |
| F1 Score | 0.629 |
| ROC-AUC | 0.995 |
| PR-AUC | 0.917 |

> Accuracy alone is not a meaningful metric on an imbalanced fraud dataset — precision, recall, F1, and PR-AUC are the metrics that matter most here.

**Red-Team Attack Detection**

| Stage | Overall Detection Rate |
|---|---|
| Before adversarial training | 11.7% |
| After 2 adversarial-training rounds | 62.0% |

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

`geo_evasion` remains the hardest attack family to detect with the current feature set — an honestly reported limitation of the prototype, not an unexplained gap.

---

## Precision / Recall Trade-Off After Adversarial Retraining

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

## Defense Command Center — Interactive Frontend

The frontend (`web/index.html`) is a self-contained dashboard that talks directly to the FastAPI backend. In it, users can:

- View the **dashboard** — model performance, fraud recall, ROC-AUC/PR-AUC, closed-loop detection improvement, and system health
- Use the **Transaction Analyzer** — submit a transaction and view its live fraud probability, risk score, and explanation
- Use the **Attack Simulator** — choose an attack family and intensity, generate an adversarial transaction, and see whether the detector catches it
- Browse the **Red-Team Arsenal** — an overview of all seven attack families and their evasion characteristics
- Review **Model Evaluation** — charts for attack detection by type, closed-loop before/after impact, ROC curve, and top risk signals (explainable AI)
- Check **System Health / API Console** — live backend status for the FastAPI service and loaded model

---

## API Reference

Based on the actual FastAPI backend:

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Returns API and model-load status |
| `/predict` | POST | Scores a single transaction and returns fraud probability, risk score, and explanation |
| `/simulate-attack` | POST | Applies a chosen Red-Team attack to a base transaction and scores the result |
| `/red-team` | POST | Runs a batch of Red-Team attacks and returns aggregate detection results |
| `/metrics` | GET | Returns pre-computed evaluation metrics for the dashboard |

**Interactive API documentation** (when running locally):

http://localhost:8000/docs



FastAPI automatically generates an OpenAPI-compatible schema and Swagger UI for all endpoints.

---

## Architecture

```text
                    ┌────────────────────────┐
                    │ Synthetic Transaction  │
                    │       Generator        │
                    └───────────┬────────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │       BLUE TEAM        │
                    │ XGBoost / RF / IF      │
                    │ Fraud Detection Engine │
                    └───────────┬────────────┘
                                │
                          Fraud / Risk Score
                                │
                                ▼
                    ┌────────────────────────┐
                    │        RED TEAM        │
                    │ 7 Adversarial Families │
                    │ Attack Simulation      │
                    └───────────┬────────────┘
                                │
                       Adversarial Transactions
                                │
                                ▼
                    ┌────────────────────────┐
                    │   Attack Detection     │
                    │   Missed Attacks       │
                    └───────────┬────────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │  Adversarial Training  │
                    │   + Model Retraining   │
                    └───────────┬────────────┘
                                │
                                └───────────► Repeat
```

---

## Project Structure

```text
mastercard-ai-defense-lab/
│
├── api/
│   └── main.py
│
├── models/
│   └── trained detectors
│
├── notebooks/
│   └── Mastercard_AI_Defense_Lab_2026.ipynb
│
├── outputs/
│   ├── figures/
│   ├── metrics/
│   └── synthetic_transactions.parquet
│
├── src/
│   ├── data_generator.py
│   ├── preprocessing.py
│   ├── blue_team.py
│   ├── red_team.py
│   ├── adversarial_training.py
│   ├── evaluation.py
│   ├── explainability.py
│   ├── demo.py
│   └── make_visualizations.py
│
├── web/
│   └── index.html
│
├── Dockerfile
├── requirements.txt
├── README.md
└── LICENSE
```

---

## Local Setup

**1. Clone the repository**

```bash
git clone https://github.com/SunnyAgrwl05/mastercard-ai-defense-lab.git
cd mastercard-ai-defense-lab
```

**2. Create a virtual environment**

```bash
python3 -m venv venv
source venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Reproduce the pipeline (optional)**

```bash
python3 src/data_generator.py
python3 src/blue_team.py
python3 src/adversarial_training.py
python3 src/make_visualizations.py
python3 src/demo.py
```

**5. Start the API**

```bash
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

**6. Open the frontend**

http://localhost:8000


**7. Open the API docs**

http://localhost:8000/docs


---

## Docker

**Build the image**

```bash
docker build -t mastercard-ai-defense-lab .
```

**Run the container**

```bash
docker run -p 8000:8000 mastercard-ai-defense-lab
```

**Open the app**


http://localhost:8000


The Docker image packages the API, the trained detector artifacts, and the frontend so the full system runs from a single container.

---

## Notebook

The repository includes a self-contained research notebook:


notebooks/Mastercard_AI_Defense_Lab_2026.ipynb



It walks through the full pipeline in order:

```text
Data Generation
      ↓
Preprocessing
      ↓
Blue-Team Training
      ↓
Red-Team Simulation
      ↓
Adversarial Training
      ↓
Evaluation
      ↓
Visualization
```

The notebook can be run locally or adapted to run in a hosted notebook environment such as Kaggle.

---

## Security & Privacy Notice

This project uses **100% synthetic data**. Specifically, this repository:

- Does **not** contain real Mastercard cardholder data
- Does **not** connect to any Mastercard production system
- Does **not** process real payment transactions
- Does **not** expose real customer information

All risk thresholds shown in the dashboard are demonstration thresholds defined for this research prototype, not production Mastercard thresholds.

---

## Limitations

This project is intended for research, education, security experimentation, and hackathon demonstration. Known limitations include:

- Synthetic rather than real-world payment data
- Simplified behavioral features compared to a production fraud stack
- Simulated, rather than observed, adversarial attack strategies
- No integration with a real payment network or card-authorization infrastructure
- Geographic evasion (`geo_evasion`) remains difficult to detect with the current feature set
- Adversarial retraining reduces precision on clean transactions, requiring careful threshold management

---

## Future Roadmap

- [ ] Real-time streaming transaction simulation
- [ ] Graph-based fraud detection
- [ ] Device fingerprint intelligence
- [ ] IP reputation signals
- [ ] Online / incremental learning
- [ ] More adaptive Red-Team agents
- [ ] Multi-model ensemble optimization
- [ ] Human-in-the-loop review queue
- [ ] Model drift monitoring
- [ ] Risk-band threshold optimization
- [ ] Authentication and role-based access control (RBAC)

---

## Tech Stack

**Machine Learning**
Python · XGBoost · Scikit-learn · SHAP · Pandas · NumPy · PyArrow

**Backend**
FastAPI · Uvicorn · OpenAPI

**Frontend**
HTML · CSS · JavaScript

**Infrastructure**
Docker · Render · GitHub

---

## Author

**Sunny Kumar**
AI / ML · Full-Stack Development · Generative AI · Cybersecurity

GitHub: https://github.com/SunnyAgrwl05

---

## License

This project is licensed under the MIT License — see [MIT License](LICENSE) for the full text.

---

## Disclaimer

Mastercard AI Defense Lab is an independent research and hackathon prototype. It is not affiliated with, endorsed by, sponsored by, or officially connected to Mastercard, except as described in the context of the relevant innovation challenge. All payment data used in this project is synthetic, and the project does not represent Mastercard's actual fraud-detection systems, thresholds, data, infrastructure, or performance.

---

<div align="center">

**AI Defense Lab — Red Team × Blue Team × Continuous Learning**
Payment security research prototype built on FastAPI, XGBoost, and SHAP.

🚀 [Live Demo](https://mastercard-ai-defense-lab.onrender.com/) · 💻 [GitHub Repository](https://github.com/SunnyAgrwl05/mastercard-ai-defense-lab)

</div>

