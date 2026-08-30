# 🛡️ Mastercard AI Defense Lab

### Red Team × Blue Team · AI-Powered Payment Fraud Defense

[🚀 Live Demo](https://mastercard-ai-defense-lab.onrender.com/) ·
[💻 GitHub](https://github.com/SunnyAgrwl05/mastercard-ai-defense-lab)

---

## 🌐 Live Defense Command Center

Experience the interactive **Red Team / Blue Team payment-security dashboard**:

### 🚀 [Open Live Demo →](https://mastercard-ai-defense-lab.onrender.com/)

The live Defense Command Center provides:

- 🔵 Blue-Team fraud detection
- 🔴 Red-Team attack simulation
- 🎯 Transaction risk scoring
- 🧠 Explainable AI
- 📊 Model performance metrics
- 🔁 Closed-loop adversarial learning
- ⚡ Real-time API interaction
- ❤️ System health monitoring

---

# 🎯 Aim of the Project

The aim of **Mastercard AI Defense Lab** is to demonstrate how an AI-powered payment-security system can continuously test and improve itself against adversarial fraud strategies.

Instead of building only a fraud detector, this project creates a **closed-loop Red Team × Blue Team security system**.

```text
Synthetic Transactions
        ↓
   Blue-Team Detector
        ↓
   Red-Team Attacks
        ↓
   Detect Missed Attacks
        ↓
 Adversarial Retraining
        ↓
 Improved Blue-Team Model
        ↓
      Repeat
```

The project explores:

- Adversarial machine learning
- Payment fraud detection
- AI security
- Explainable AI
- Adversarial attack simulation
- Continuous model improvement
- Model resilience
- Red Team vs Blue Team security workflows

This is a research and innovation prototype built using fully synthetic payment data.

---

## ⚡ What Makes It Different?

Traditional fraud detection asks:

> "Can the model detect fraud?"

AI Defense Lab asks:

> "Can the model survive an attacker that actively searches for its weaknesses?"

The system combines:

- 🔵 **Blue Team** — machine-learning fraud detection
- 🔴 **Red Team** — adaptive adversarial attack simulation
- 🔁 **Closed Loop** — missed attacks become new training examples
- 🧠 **Explainable AI** — risk explanations and feature importance
- 📊 **Model Evaluation** — ROC-AUC, PR-AUC, precision, recall and F1
- ⚡ **FastAPI** — real-time prediction and attack-simulation API
- 🌐 **Interactive Web Console** — security command center

---

## 🔵 Blue Team

The Blue Team acts as the payment fraud-defense layer.

It evaluates transaction characteristics such as:

- Transaction amount
- Historical spending baseline
- Merchant category
- Device information
- Geographic distance
- Transaction velocity
- Failed transactions
- Transaction time
- Behavioral patterns

The project evaluates multiple machine-learning approaches:

- XGBoost
- Random Forest
- Isolation Forest

The strongest detector is selected based on validation performance.

### Example Risk Output

```text
Risk Score: 32.9 / 100

Classification: Legitimate
Risk Level: Medium

Contributing Signals:
• Merchant category
• Transaction amount
• Recent spending behaviour
• Time of transaction
```

---

## 🔴 Red Team

The Red Team attempts to bypass the Blue-Team detector using seven synthetic adversarial attack families.

| # | Attack Family | Objective |
|---|----------------|-----------|
| 01 | Amount Manipulation | Stay below amount-based thresholds |
| 02 | Velocity Attack | Exploit transaction-frequency weaknesses |
| 03 | Merchant Switching | Spread suspicious behaviour across merchants |
| 04 | Geographic Evasion | Avoid obvious location anomalies |
| 05 | Account Takeover | Simulate sudden account/device/location changes |
| 06 | Low-and-Slow | Perform many small transactions |
| 07 | Behavioral Mimicry | Mimic the victim's historical spending |

The Red Team adapts its attack strategy according to weaknesses observed in the detector.

---

## 🔁 Closed-Loop Adversarial Learning

The core idea of the project is continuous adversarial improvement.

### Step 1 — Generate Attacks

```text
Generate synthetic adversarial transactions
                    ↓
             Attack the detector
```

### Step 2 — Detect Weaknesses

```text
Blue Team scores attacks
          ↓
Identify missed attacks
```

### Step 3 — Adversarial Training

```text
Missed attacks
      ↓
Add to training dataset
      ↓
Retrain detector
```

### Step 4 — Test Again

```text
Generate fresh unseen attacks
            ↓
      Evaluate detector
            ↓
      Measure resilience
```

This creates the continuous:

```text
Generate
   ↓
Attack
   ↓
Detect
   ↓
Learn
   ↓
Retrain
   ↓
Attack Again
```

cycle.

---

## 📊 Project Results

Results from the project's synthetic training and evaluation run.

### Dataset

- 160,265 synthetic transactions
- 900 synthetic accounts
- 80 days of simulated activity
- 2.00% synthetic fraud prevalence
- Random seed: 42 / 7

All data is synthetic and generated specifically for this research prototype.

### 🔵 Blue-Team Baseline

| Metric | Result |
|--------|--------|
| Model | XGBoost |
| Accuracy | 97.7% |
| Precision | 47.1% |
| Recall | 94.7% |
| F1 | 62.9% |
| ROC-AUC | 0.995 |
| PR-AUC | 0.917 |

Accuracy alone can be misleading on highly imbalanced fraud datasets.

For this reason, the project focuses strongly on:

- Precision
- Recall
- F1
- ROC-AUC
- PR-AUC

### 🔴 Red-Team Detection Results

#### Before Adversarial Training

The initial detector identified only:

**11.7% overall adversarial attack detection**

Average risk score: **13.1 / 100**

| Attack Family | Detection Rate |
|---------------|-----------------|
| geo_evasion | 0.7% |
| velocity_attack | 1.3% |
| low_and_slow | 2.0% |
| amount_manipulation | 4.7% |
| merchant_switching | 8.0% |
| behavioral_mimicry | 8.0% |
| account_takeover | 57.3% |

This demonstrates that a strong conventional fraud detector can still have significant blind spots against adversarial strategies.

#### 🚀 After 2 Adversarial-Training Rounds

After feeding previously missed attacks back into training:

**Overall attack detection increased to 62.0%**

Average risk score: **63.8 / 100**

A total of 1,353 previously missed adversarial examples were added back into training.

| Attack Family | Detection Rate |
|---------------|-----------------|
| geo_evasion | 5.3% |
| behavioral_mimicry | 39.3% |
| amount_manipulation | 42.7% |
| merchant_switching | 49.3% |
| low_and_slow | 98.0% |
| account_takeover | 99.3% |
| velocity_attack | 100.0% |

### ⚖️ Honest Trade-Off

Adversarial retraining improved attack coverage, but it also changed the decision boundary on clean transactions.

| Metric | Before | After |
|--------|--------|-------|
| Precision | 0.471 | 0.315 |
| Recall | 0.947 | 0.956 |
| F1 | 0.629 | 0.474 |
| ROC-AUC | 0.995 | 0.990 |
| PR-AUC | 0.917 | 0.906 |

This is an important result.

The system demonstrates that improving adversarial coverage can increase false-positive pressure on legitimate transactions.

A production system would therefore consider:

- Threshold recalibration
- Cost-sensitive learning
- Risk-band-specific thresholds
- Human review queues
- Continuous monitoring

### 🌍 Geographic Evasion Limitation

`geo_evasion` remains one of the hardest attack families for the current feature set.

This reflects a genuine limitation of the prototype.

A production-grade system could improve geographic fraud detection using:

- Device fingerprinting
- IP reputation
- Network intelligence
- Location consistency
- Account graph analysis
- Behavioral profiling

---

## 🧠 Explainable AI

The system provides explanations for why a transaction receives a particular risk score.

The project includes:

- SHAP-based feature importance
- Top risk signals
- Plain-English risk narratives
- Model evaluation visualizations

### Example

```text
Risk Score: 87.4 / 100

Risk Level: High

Main Contributing Signals:
• Unusual transaction amount
• High transaction velocity
• Geographic distance
• Failed transaction activity
```

The objective is not only to detect suspicious transactions, but also to make the model's reasoning easier to understand.

---

## 🌐 Defense Command Center

The frontend provides an interactive payment-security dashboard.

### Dashboard

The dashboard displays:

- Model performance
- Fraud recall
- ROC-AUC
- PR-AUC
- Attack detection
- Closed-loop improvement
- Threat activity
- API status
- Model health

### 🎯 Transaction Analyzer

Transactions can be submitted to:

```
POST /predict
```

The API returns information such as:

- Fraud probability
- Risk score
- Classification
- Risk level
- Explanation
- Model information
- Raw prediction output

### 🔴 Attack Simulator

The frontend can simulate adversarial payment attacks using:

```
POST /simulate-attack
```

This allows users to test whether the Blue Team can identify different attack strategies.

### 🧪 Red-Team Batch Testing

The project exposes:

```
POST /red-team
```

to generate and evaluate a batch of synthetic attacks across the seven attack families.

### 📊 Metrics

The dashboard can retrieve evaluation results using:

```
GET /metrics
```

---

## 🔌 API Reference

FastAPI provides the following endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | API and loaded-model health |
| `/predict` | POST | Score a transaction |
| `/simulate-attack` | POST | Simulate and score an adversarial transaction |
| `/red-team` | POST | Generate and evaluate Red-Team attacks |
| `/metrics` | GET | Return project evaluation metrics |

### 📖 API Documentation

When running locally:

```
http://localhost:8000/docs
```

FastAPI automatically provides an OpenAPI-compatible API documentation interface.

---

## 🏗️ Architecture

```text
                    ┌────────────────────────┐
                    │ Synthetic Transactions │
                    │       Generator        │
                    └───────────┬────────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │       BLUE TEAM        │
                    │ XGBoost / RF / IF      │
                    │ Fraud Detection        │
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
                    │ Adversarial Training   │
                    │ + Model Retraining     │
                    └───────────┬────────────┘
                                │
                                └──────────────► Repeat
```

---

## 📁 Project Structure

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

## 💻 Run Locally

### 1. Clone Repository

```bash
git clone https://github.com/SunnyAgrwl05/mastercard-ai-defense-lab.git
cd mastercard-ai-defense-lab
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Generate Synthetic Data

```bash
python3 src/data_generator.py
```

### 5. Train Blue-Team Baseline

```bash
python3 src/blue_team.py
```

### 6. Run Adversarial Training

```bash
python3 src/adversarial_training.py
```

### 7. Generate Evaluation Charts

```bash
python3 src/make_visualizations.py
```

### 8. Run End-to-End Demo

```bash
python3 src/demo.py
```

### 9. Start FastAPI

```bash
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Open:

```
http://localhost:8000
```

API documentation:

```
http://localhost:8000/docs
```

---

## 🐳 Run with Docker

### Build

```bash
docker build -t mastercard-ai-defense-lab .
```

### Run

```bash
docker run -p 8000:8000 mastercard-ai-defense-lab
```

Then open:

```
http://localhost:8000
```

The Docker image contains the required application files and trained detector artifacts.

---

## 📓 Notebook

The project includes a self-contained research notebook:

```
notebooks/Mastercard_AI_Defense_Lab_2026.ipynb
```

The notebook demonstrates:

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

The notebook can be run locally or adapted for a Kaggle environment.

---

## 🔐 Security & Privacy Notice

⚠️ **This project uses 100% synthetic data.**

All transactions, customers, accounts and attack traces are artificially generated.

This repository:

- Does not contain real Mastercard cardholder data.
- Does not connect to Mastercard production systems.
- Does not process real payment transactions.
- Does not expose real customer information.
- Does not claim production-level fraud detection performance.

Risk thresholds used by the dashboard are demonstration thresholds only.

---

## ⚠️ Limitations

This project is intended for:

- Research
- Education
- Security experimentation
- AI/ML experimentation
- Hackathon demonstration

Important limitations include:

- Synthetic rather than real-world payment data
- Simplified behavioral features
- Simulated attack strategies
- No production payment-network integration
- No real-time banking/card authorization infrastructure
- Geographic spoofing remains difficult to detect
- Adversarial retraining can reduce precision on clean transactions

A production implementation would require additional:

- Device intelligence
- IP reputation
- Network intelligence
- Account graph analysis
- Real-time behavioral profiling
- Cost-sensitive learning
- Human review workflows
- Model monitoring
- Drift detection
- Threshold optimization

---

## 🧰 Tech Stack

**Machine Learning**
- Python
- XGBoost
- Scikit-learn
- SHAP
- Pandas
- NumPy
- PyArrow

**Backend**
- FastAPI
- Uvicorn
- OpenAPI

**Frontend**
- HTML
- CSS
- JavaScript
- Interactive Security Dashboard

**Infrastructure**
- Docker
- Render
- GitHub

---

## 🚀 Future Roadmap

- [ ] Real-time streaming transaction simulation
- [ ] Graph-based fraud detection
- [ ] Device fingerprint intelligence
- [ ] IP reputation signals
- [ ] Online learning
- [ ] More adaptive Red-Team agents
- [ ] Multi-model ensemble optimization
- [ ] Human-in-the-loop review queue
- [ ] Model drift monitoring
- [ ] Advanced SHAP visualizations
- [ ] Authentication
- [ ] Role-based security console
- [ ] Real-time alerting
- [ ] Security audit logs

---

## 👨‍💻 Author

**Sunny Kumar**

AI / ML · Full-Stack Development · Generative AI · Cybersecurity

Built as an experimental Red Team × Blue Team payment-security research lab.

GitHub: [https://github.com/SunnyAgrwl05](https://github.com/SunnyAgrwl05)

---

## 📄 License

This project is licensed under the **MIT License**.

MIT License allows users to:

- Use the software
- Copy the software
- Modify the software
- Distribute the software
- Use it commercially

Subject to the conditions of the MIT License.

See the `LICENSE` file in this repository for the complete license text.

---

## ⚖️ Disclaimer

Mastercard AI Defense Lab is an independent research and innovation prototype.

The project is not affiliated with, endorsed by, sponsored by, or officially connected to Mastercard unless explicitly stated by the relevant challenge organizers.

All payment data used in this project is synthetic.

The project should not be interpreted as a production fraud-detection system or as representing Mastercard's actual fraud-detection systems, thresholds, data, infrastructure, or performance.

---

<div align="center">

### 🛡️ AI Defense Lab
**Red Team × Blue Team × Continuous Learning**

Payment Security Research Prototype

Built with: FastAPI · XGBoost · Scikit-learn · SHAP · Python · JavaScript · Docker

🚀 [Live Demo](https://mastercard-ai-defense-lab.onrender.com/) · 💻 [GitHub Repository](https://github.com/SunnyAgrwl05/mastercard-ai-defense-lab)

Built with ❤️ by Sunny Kumar

</div>