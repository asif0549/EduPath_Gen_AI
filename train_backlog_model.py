"""Train and persist the EduPath high-backlog-risk classifier."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


ROOT_DIR = Path(__file__).resolve().parent
DATA_PATH = ROOT_DIR / "data" / "students_dataset.csv"
MODEL_DIR = ROOT_DIR / "models"
MODEL_PATH = MODEL_DIR / "backlog_risk_model.joblib"
METRICS_PATH = MODEL_DIR / "backlog_risk_model_metrics.json"

FEATURES = [
    "attendance",
    "cgpa",
    "aptitude_score",
    "coding_score",
    "communication_score",
    "mock_exam_score",
]
SOURCE_TARGET = "backlogs"
TARGET = "backlog_risk"
HIGH_RISK_THRESHOLD = 2
RANDOM_STATE = 42

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def load_and_validate_data(path: Path) -> pd.DataFrame:
    """Load data, validate its contract, and derive a leakage-free label."""
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    data = pd.read_csv(path)
    required = set(FEATURES + [SOURCE_TARGET])
    missing = sorted(required.difference(data.columns))
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")
    if data[list(required)].isnull().any().any():
        null_counts = data[list(required)].isnull().sum()
        raise ValueError(f"Training columns contain nulls:\n{null_counts[null_counts > 0]}")
    if (data[SOURCE_TARGET] < 0).any():
        raise ValueError("backlogs cannot contain negative values")

    data = data.copy()
    data[TARGET] = (data[SOURCE_TARGET] >= HIGH_RISK_THRESHOLD).astype(int)
    if data[TARGET].nunique() < 2:
        raise ValueError("Derived backlog_risk target must contain both classes")
    return data


def build_pipeline() -> Pipeline:
    classifier = RandomForestClassifier(
        n_estimators=300,
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        random_state=RANDOM_STATE,
        n_jobs=1,
    )
    return Pipeline([("classifier", classifier)])


def train() -> None:
    data = load_and_validate_data(DATA_PATH)
    x_train, x_test, y_train, y_test = train_test_split(
        data[FEATURES],
        data[TARGET],
        test_size=0.20,
        random_state=RANDOM_STATE,
        stratify=data[TARGET],
    )

    model = build_pipeline()
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    high_risk_probabilities = model.predict_proba(x_test)[:, 1]

    report = classification_report(
        y_test,
        predictions,
        labels=[0, 1],
        target_names=["Low Risk", "High Risk"],
        output_dict=True,
        zero_division=0,
    )
    metrics = {
        "model": "RandomForestClassifier",
        "target_definition": f"High Risk when backlogs >= {HIGH_RISK_THRESHOLD}",
        "dataset_rows": len(data),
        "train_rows": len(x_train),
        "test_rows": len(x_test),
        "features": FEATURES,
        "class_distribution": {
            "Low Risk": int((data[TARGET] == 0).sum()),
            "High Risk": int((data[TARGET] == 1).sum()),
        },
        "accuracy": accuracy_score(y_test, predictions),
        "roc_auc": roc_auc_score(y_test, high_risk_probabilities),
        "classification_report": report,
        "confusion_matrix": {
            "labels": ["Low Risk", "High Risk"],
            "values": confusion_matrix(y_test, predictions, labels=[0, 1]).tolist(),
        },
        "random_state": RANDOM_STATE,
    }

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    logger.info("High-risk rows: %d of %d", metrics["class_distribution"]["High Risk"], len(data))
    logger.info("Test accuracy: %.4f", metrics["accuracy"])
    logger.info("Test ROC AUC: %.4f", metrics["roc_auc"])
    logger.info("Saved model to %s", MODEL_PATH)
    logger.info("Saved metrics to %s", METRICS_PATH)


if __name__ == "__main__":
    train()
