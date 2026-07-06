"""Train and persist the EduPath exam-readiness classifier."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


ROOT_DIR = Path(__file__).resolve().parent
DATA_PATH = ROOT_DIR / "data" / "students_dataset.csv"
MODEL_DIR = ROOT_DIR / "models"
MODEL_PATH = MODEL_DIR / "exam_readiness_model.joblib"
METRICS_PATH = MODEL_DIR / "exam_readiness_model_metrics.json"

NUMERIC_FEATURES = [
    "attendance",
    "cgpa",
    "aptitude_score",
    "mock_exam_score",
    "backlogs",
]
CATEGORICAL_FEATURES = ["exam_selected"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TARGET = "exam_readiness"
READINESS_SCORE = "exam_readiness_score"
RANDOM_STATE = 42

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def load_and_validate_data(path: Path) -> pd.DataFrame:
    """Load data and derive a documented readiness proxy label."""
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    data = pd.read_csv(path)
    required = set(FEATURES)
    missing = sorted(required.difference(data.columns))
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")
    if data[list(required)].isnull().any().any():
        null_counts = data[list(required)].isnull().sum()
        raise ValueError(f"Training columns contain nulls:\n{null_counts[null_counts > 0]}")

    numeric_ranges = {
        "attendance": (0, 100),
        "cgpa": (0, 10),
        "aptitude_score": (0, 100),
        "mock_exam_score": (0, 100),
    }
    for column, (minimum, maximum) in numeric_ranges.items():
        if not data[column].between(minimum, maximum).all():
            raise ValueError(f"{column} must be between {minimum} and {maximum}")
    if (data["backlogs"] < 0).any():
        raise ValueError("backlogs cannot contain negative values")

    data = data.copy()
    # Proxy until real exam attempt/result labels are collected.
    data[READINESS_SCORE] = (
        0.50 * data["mock_exam_score"]
        + 0.25 * data["aptitude_score"]
        + 0.15 * data["attendance"]
        + 0.10 * (data["cgpa"] * 10)
        - 2.0 * data["backlogs"].clip(upper=5)
    ).clip(lower=0, upper=100)
    data[TARGET] = pd.cut(
        data[READINESS_SCORE],
        bins=[-0.01, 49.99, 69.99, 100],
        labels=["Needs Preparation", "Developing", "Ready"],
    ).astype(str)
    if data[TARGET].nunique() < 2:
        raise ValueError("Derived exam_readiness target must contain multiple classes")
    return data


def build_pipeline() -> Pipeline:
    preprocessing = ColumnTransformer(
        transformers=[
            ("numeric", "passthrough", NUMERIC_FEATURES),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL_FEATURES,
            ),
        ]
    )
    classifier = RandomForestClassifier(
        n_estimators=300,
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        random_state=RANDOM_STATE,
        n_jobs=1,
    )
    return Pipeline([("preprocessing", preprocessing), ("classifier", classifier)])


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
    labels = ["Needs Preparation", "Developing", "Ready"]
    report = classification_report(
        y_test, predictions, labels=labels, output_dict=True, zero_division=0
    )
    distribution = data[TARGET].value_counts()
    metrics = {
        "model": "RandomForestClassifier",
        "target_definition": (
            "Proxy score: 50% mock exam + 25% aptitude + 15% attendance + "
            "10% normalized CGPA - 2 points per backlog; bands <50, 50-69.99, >=70"
        ),
        "dataset_rows": len(data),
        "train_rows": len(x_train),
        "test_rows": len(x_test),
        "features": FEATURES,
        "class_distribution": {label: int(distribution.get(label, 0)) for label in labels},
        "accuracy": accuracy_score(y_test, predictions),
        "classification_report": report,
        "confusion_matrix": {
            "labels": labels,
            "values": confusion_matrix(y_test, predictions, labels=labels).tolist(),
        },
        "random_state": RANDOM_STATE,
    }

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    logger.info("Class distribution: %s", metrics["class_distribution"])
    logger.info("Test accuracy: %.4f", metrics["accuracy"])
    logger.info("Saved model to %s", MODEL_PATH)
    logger.info("Saved metrics to %s", METRICS_PATH)


if __name__ == "__main__":
    train()
