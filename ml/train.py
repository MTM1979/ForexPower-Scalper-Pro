# ml/train.py
from __future__ import annotations
import argparse
import logging
from pathlib import Path
import joblib
import json
from typing import Optional
import pandas as pd
import numpy as np

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, roc_auc_score, precision_score, recall_score
import lightgbm as lgb

from ml.data_prep.dataset_builder import DatasetBuilder

logger = logging.getLogger("ml.train")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def load_dataset(path: Path) -> tuple[pd.DataFrame, pd.Series]:
    if path.suffix in [".parquet", ".pq"]:
        df = pd.read_parquet(path)
    else:
        df = pd.read_csv(path)
    if "__label__" not in df.columns:
        raise ValueError("Dataset must contain '__label__' column")
    y = df["__label__"].astype(int)
    X = df.drop(columns=["__label__"])
    return X, y


def build_pipeline() -> Pipeline:
    clf = lgb.LGBMClassifier(
        objective="binary",
        n_jobs=-1,
        random_state=42,
        verbosity=-1,
    )
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", clf),
    ])
    return pipeline


def run_training(
    dataset_path: Path,
    out_model: Path,
    test_size: float = 0.2,
    grid_search: bool = True,
    cv: int = 3,
    n_jobs: int = -1,
) -> None:
    X, y = load_dataset(dataset_path)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, stratify=y, random_state=42)

    pipeline = build_pipeline()
    if grid_search:
        param_grid = {
            "clf__num_leaves": [31, 63],
            "clf__n_estimators": [100, 300],
            "clf__learning_rate": [0.05, 0.1],
        }
        gs = GridSearchCV(pipeline, param_grid, cv=cv, n_jobs=n_jobs, verbose=1, scoring="roc_auc")
        gs.fit(X_train, y_train)
        best = gs.best_estimator_
        logger.info("GridSearchCV best params: %s", gs.best_params_)
    else:
        best = pipeline
        best.fit(X_train, y_train)

    # Predict on test
    y_pred = best.predict(X_test)
    y_proba = best.predict_proba(X_test)[:, 1] if hasattr(best, "predict_proba") else None

    # Metrics
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    roc = roc_auc_score(y_test, y_proba) if y_proba is not None else float("nan")

    metrics = {
        "accuracy": float(acc),
        "precision": float(prec),
        "recall": float(rec),
        "roc_auc": float(roc),
    }
    logger.info("Test metrics: %s", metrics)

    # Save model and metadata
    out_model.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(best, out_model)
    logger.info("Saved trained model pipeline to %s", out_model)

    # Save metrics next to model
    meta_file = out_model.with_suffix(".metrics.json")
    with open(meta_file, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info("Saved metrics to %s", meta_file)


def main():
    parser = argparse.ArgumentParser(description="Train ML model for ForexScalperPro")
    parser.add_argument("--dataset", required=True, help="Path to dataset (.parquet or .csv) with __label__ column")
    parser.add_argument("--out", required=True, help="Path to save trained model (joblib). e.g. models/model.joblib")
    parser.add_argument("--no-grid", action="store_true", help="Disable grid search (faster)")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--cv", type=int, default=3)
    args = parser.parse_args()

    run_training(
        dataset_path=Path(args.dataset),
        out_model=Path(args.out),
        test_size=args.test_size,
        grid_search=not args.no_grid,
        cv=args.cv,
    )


if __name__ == "__main__":
    main()
