"""
make_visualizations.py
=======================
Generates all 10 required visualizations FROM THE ACTUAL SAVED RESULTS of the
pipeline (data generator -> blue team -> red team -> closed loop). No numbers
here are invented; every chart reads from files written by the earlier stages.
"""
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, roc_curve, precision_recall_curve

sns.set_theme(style="whitegrid")
BASE = "/home/claude/mastercard-ai-defense-lab"
FIG = f"{BASE}/outputs/figures"

import sys
sys.path.insert(0, f"{BASE}/src")
from blue_team import BlueTeamDetector

df = pd.read_parquet(f"{BASE}/outputs/synthetic_transactions.parquet")
split = joblib.load(f"{BASE}/models/split_data.pkl")
detector_before = BlueTeamDetector.load(f"{BASE}/models/fraud_detector.pkl")
detector_after = BlueTeamDetector.load(f"{BASE}/models/fraud_detector_after_closed_loop.pkl")

round1_summary = pd.read_csv(f"{BASE}/outputs/metrics/round1_before_attack_summary.csv")
final_summary = pd.read_csv(f"{BASE}/outputs/metrics/final_after_attack_summary.csv")
with open(f"{BASE}/outputs/metrics/closed_loop_summary.json") as f:
    closed_loop = json.load(f)

# ---------------------------------------------------------------
# 1. Class distribution
# ---------------------------------------------------------------
plt.figure(figsize=(6, 4))
counts = df["fraud_label"].value_counts().rename({0: "Legitimate", 1: "Fraud"})
sns.barplot(x=counts.index, y=counts.values, palette=["#2e7d32", "#c62828"])
for i, v in enumerate(counts.values):
    plt.text(i, v, f"{v:,}\n({v/len(df)*100:.2f}%)", ha="center", va="bottom", fontsize=10)
plt.title("Class Distribution: Legitimate vs Fraud (Synthetic Base Dataset)")
plt.ylabel("Number of transactions")
plt.tight_layout()
plt.savefig(f"{FIG}/01_class_distribution.png", dpi=140)
plt.close()

# ---------------------------------------------------------------
# 2. Fraud vs legitimate — amount distribution
# ---------------------------------------------------------------
plt.figure(figsize=(7, 4.5))
sample = df.sample(min(60000, len(df)), random_state=1)
sns.kdeplot(np.log1p(sample.loc[sample.fraud_label == 0, "amount"]), label="Legitimate", fill=True, alpha=0.4)
sns.kdeplot(np.log1p(sample.loc[sample.fraud_label == 1, "amount"]), label="Fraud", fill=True, alpha=0.4)
plt.xlabel("log(1 + transaction amount)")
plt.title("Transaction Amount Distribution: Fraud vs Legitimate")
plt.legend()
plt.tight_layout()
plt.savefig(f"{FIG}/02_fraud_vs_legit_amount.png", dpi=140)
plt.close()

# ---------------------------------------------------------------
# 3. Confusion matrix (test set, initial detector)
# ---------------------------------------------------------------
proba_test = detector_before.predict_proba(split.X_test)
pred_test = (proba_test >= 0.5).astype(int)
cm = confusion_matrix(split.y_test, pred_test)
plt.figure(figsize=(5, 4.5))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=["Legit", "Fraud"], yticklabels=["Legit", "Fraud"])
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title(f"Confusion Matrix — Test Set ({detector_before.best_model_name})")
plt.tight_layout()
plt.savefig(f"{FIG}/03_confusion_matrix.png", dpi=140)
plt.close()

# ---------------------------------------------------------------
# 4. ROC curve
# ---------------------------------------------------------------
fpr, tpr, _ = roc_curve(split.y_test, proba_test)
plt.figure(figsize=(5.5, 4.5))
plt.plot(fpr, tpr, label=f"{detector_before.best_model_name} (AUC={np.trapezoid(tpr, fpr):.3f})", color="#1565c0")
plt.plot([0, 1], [0, 1], linestyle="--", color="grey", label="Random")
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC Curve — Test Set")
plt.legend()
plt.tight_layout()
plt.savefig(f"{FIG}/04_roc_curve.png", dpi=140)
plt.close()

# ---------------------------------------------------------------
# 5. Precision-Recall curve
# ---------------------------------------------------------------
prec, rec, _ = precision_recall_curve(split.y_test, proba_test)
plt.figure(figsize=(5.5, 4.5))
plt.plot(rec, prec, color="#ad1457")
plt.xlabel("Recall")
plt.ylabel("Precision")
plt.title("Precision-Recall Curve — Test Set (highly imbalanced data)")
plt.tight_layout()
plt.savefig(f"{FIG}/05_precision_recall_curve.png", dpi=140)
plt.close()

# ---------------------------------------------------------------
# 6. Feature importance
# ---------------------------------------------------------------
imp = detector_before.feature_importance().head(15).sort_values()
plt.figure(figsize=(7, 6))
plt.barh(imp.index, imp.values, color="#00897b")
plt.title(f"Top 15 Feature Importances ({detector_before.best_model_name})")
plt.xlabel("Importance")
plt.tight_layout()
plt.savefig(f"{FIG}/06_feature_importance.png", dpi=140)
plt.close()

# ---------------------------------------------------------------
# 7. Attack detection rate by attack type (before closed loop)
# ---------------------------------------------------------------
r1 = round1_summary.sort_values("detection_rate")
plt.figure(figsize=(8, 5))
plt.barh(r1["attack_type"], r1["detection_rate"] * 100, color="#e65100")
plt.xlabel("Detection rate (%)")
plt.title("Red-Team Attack Detection Rate by Type — BEFORE Closed-Loop Training")
plt.xlim(0, 100)
for i, v in enumerate(r1["detection_rate"] * 100):
    plt.text(v + 1, i, f"{v:.1f}%", va="center")
plt.tight_layout()
plt.savefig(f"{FIG}/07_attack_detection_rate_before.png", dpi=140)
plt.close()

# ---------------------------------------------------------------
# 8. Before vs after adversarial training (per attack type + overall)
# ---------------------------------------------------------------
merged = round1_summary[["attack_type", "detection_rate"]].rename(columns={"detection_rate": "before"})
merged = merged.merge(final_summary[["attack_type", "detection_rate"]].rename(columns={"detection_rate": "after"}), on="attack_type")
merged = merged.sort_values("before")
x = np.arange(len(merged))
width = 0.38
plt.figure(figsize=(9, 5.5))
plt.bar(x - width/2, merged["before"] * 100, width, label="Before closed-loop training", color="#c62828")
plt.bar(x + width/2, merged["after"] * 100, width, label="After closed-loop training", color="#2e7d32")
plt.xticks(x, merged["attack_type"], rotation=30, ha="right")
plt.ylabel("Detection rate (%)")
plt.title("Attack Detection Rate: Before vs After Adversarial Closed-Loop Training")
plt.legend()
plt.tight_layout()
plt.savefig(f"{FIG}/08_before_vs_after_closed_loop.png", dpi=140)
plt.close()

# ---------------------------------------------------------------
# 9. Risk score distribution (test set, after detector)
# ---------------------------------------------------------------
proba_after_test = detector_after.predict_proba(split.X_test)
risk_scores = np.clip(proba_after_test * 100, 0, 100)
plt.figure(figsize=(7, 4.5))
sns.histplot(risk_scores[split.y_test.values == 0], bins=40, color="#2e7d32", label="Legitimate", stat="density", alpha=0.5)
sns.histplot(risk_scores[split.y_test.values == 1], bins=40, color="#c62828", label="Fraud", stat="density", alpha=0.5)
for edge in [30, 60, 80]:
    plt.axvline(edge, color="grey", linestyle="--", linewidth=1)
plt.xlabel("Risk score (0-100)")
plt.title("Risk-Score Distribution — Final Detector on Test Set")
plt.legend()
plt.tight_layout()
plt.savefig(f"{FIG}/09_risk_score_distribution.png", dpi=140)
plt.close()

# ---------------------------------------------------------------
# 10. Red-Team attack success rate (= 1 - detection rate), before vs after
# ---------------------------------------------------------------
merged["success_before"] = (1 - merged["before"]) * 100
merged["success_after"] = (1 - merged["after"]) * 100
plt.figure(figsize=(9, 5.5))
plt.bar(x - width/2, merged["success_before"], width, label="Before closed-loop", color="#6a1b9a")
plt.bar(x + width/2, merged["success_after"], width, label="After closed-loop", color="#9575cd")
plt.xticks(x, merged["attack_type"], rotation=30, ha="right")
plt.ylabel("Attack success rate (%) [= undetected]")
plt.title("Red-Team Attack Success Rate by Type — Before vs After")
plt.legend()
plt.tight_layout()
plt.savefig(f"{FIG}/10_attack_success_rate.png", dpi=140)
plt.close()

print("All 10 visualizations saved to", FIG)
import os
print(sorted(os.listdir(FIG)))
