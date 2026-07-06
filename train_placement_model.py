"""Train and persist the EduPath placement-status classifier."""

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
MODEL_PATH = MODEL_DIR / "placement_model.joblib"
METRICS_PATH = MODEL_DIR / "placement_model_metrics.json"

TARGET = "placement_status"
NUMERIC_FEATURES = [
    "attendance",
    "cgpa",
    "aptitude_score",
    "coding_score",
    "communication_score",
    "mock_exam_score",
    "backlogs",
]
CATEGORICAL_FEATURES = ["career_interest"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
RANDOM_STATE = 42

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def load_and_validate_data(path: Path) -> pd.DataFrame:
    """Load training data and fail early when its contract is violated."""
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    data = pd.read_csv(path)
    required = set(FEATURES + [TARGET])
    missing = sorted(required.difference(data.columns))
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")
    if data[list(required)].isnull().any().any():
        null_counts = data[list(required)].isnull().sum()
        raise ValueError(f"Training columns contain nulls:\n{null_counts[null_counts > 0]}")
    if data[TARGET].nunique() < 2:
        raise ValueError("placement_status must contain at least two classes")

    return data


def build_pipeline() -> Pipeline:
    """Build preprocessing and classifier as one inference-safe artifact."""
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

    report = classification_report(y_test, predictions, output_dict=True, zero_division=0)
    labels = sorted(data[TARGET].unique().tolist())
    metrics = {
        "model": "RandomForestClassifier",
        "dataset_rows": len(data),
        "train_rows": len(x_train),
        "test_rows": len(x_test),
        "features": FEATURES,
        "classes": labels,
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

    logger.info("Trained on %d rows; tested on %d rows", len(x_train), len(x_test))
    logger.info("Test accuracy: %.4f", metrics["accuracy"])
    logger.info("Saved model to %s", MODEL_PATH)
    logger.info("Saved metrics to %s", METRICS_PATH)


if __name__ == "__main__":
    train()
