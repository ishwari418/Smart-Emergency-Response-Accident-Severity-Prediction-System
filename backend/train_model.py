"""Train and evaluate the accident severity classification pipeline."""

import json
import sys

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from config import (
    CATEGORICAL_FEATURES,
    DATASET_PATH,
    FEATURE_COLUMNS,
    METRICS_PATH,
    MODEL_DIR,
    MODEL_PATH,
    NUMERIC_FEATURES,
    SEVERITY_LABELS,
)


def train() -> dict:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at {DATASET_PATH}. Run python generate_dataset.py first.")
    data = pd.read_csv(DATASET_PATH)
    required = set(FEATURE_COLUMNS + ["severity"])
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Dataset is missing required training columns: {sorted(missing)}")
    if not data["severity"].isin(SEVERITY_LABELS).all():
        raise ValueError("severity must contain only labels 1, 2, 3, and 4")
    if data["severity"].isna().any():
        raise ValueError("severity cannot contain missing values")

    x = data[FEATURE_COLUMNS].copy()
    y = data["severity"].astype(int)
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42, stratify=y
    )
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )
    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=160,
                    min_samples_leaf=4,
                    max_leaf_nodes=768,
                    class_weight="balanced_subsample",
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    labels = sorted(SEVERITY_LABELS)
    report = classification_report(
        y_test,
        predictions,
        labels=labels,
        output_dict=True,
        zero_division=0,
    )
    metrics = {
        "model_name": "Random Forest Classifier",
        "target": "severity",
        "class_labels": {str(key): value for key, value in SEVERITY_LABELS.items()},
        "feature_columns": FEATURE_COLUMNS,
        "accuracy": float(accuracy_score(y_test, predictions)),
        "macro_precision": float(precision_score(y_test, predictions, average="macro", zero_division=0)),
        "macro_recall": float(recall_score(y_test, predictions, average="macro", zero_division=0)),
        "macro_f1": float(f1_score(y_test, predictions, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_test, predictions, average="weighted", zero_division=0)),
        "confusion_matrix": confusion_matrix(y_test, predictions, labels=labels).tolist(),
        "classification_report": {
            str(SEVERITY_LABELS[label]): {
                key: (int(value) if key == "support" else float(value))
                for key, value in report[str(label)].items()
            }
            for label in labels
        },
        "training_records": int(len(x_train)),
        "test_records": int(len(x_test)),
        "total_records": int(len(data)),
        "labels_order": labels,
    }

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH, compress=3)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Trained {metrics['model_name']} on {len(x_train):,} records.")
    print(f"Held-out test records: {len(x_test):,}")
    print(
        f"Accuracy: {metrics['accuracy']:.4f} | Macro F1: {metrics['macro_f1']:.4f} "
        f"| Weighted F1: {metrics['weighted_f1']:.4f}"
    )
    print("Per-class report:")
    print(pd.DataFrame(metrics["classification_report"]).T.to_string())
    print(f"Saved model: {MODEL_PATH}")
    print(f"Saved metrics: {METRICS_PATH}")
    return metrics


if __name__ == "__main__":
    try:
        train()
    except Exception as error:
        print(f"Training failed: {error}", file=sys.stderr)
        raise
