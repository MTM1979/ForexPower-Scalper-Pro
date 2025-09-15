# ml/predict.py
from __future__ import annotations
import argparse
from pathlib import Path
import joblib
import pandas as pd
import logging
from typing import Tuple

logger = logging.getLogger("ml.predict")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def load_pipeline(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")
    pipeline = joblib.load(path)
    return pipeline


def prepare_input(df: pd.DataFrame):
    """Minimal validation: pipeline expects numerical columns present in training X."""
    # The pipeline scaler/estimator will error if columns don't match. We just pass through.
    return df.copy()


def predict(df: pd.DataFrame, model_path: Path) -> pd.DataFrame:
    pipeline = load_pipeline(model_path)
    X = prepare_input(df)
    preds = pipeline.predict(X)
    proba = pipeline.predict_proba(X)[:, 1] if hasattr(pipeline, "predict_proba") else None
    out = df.reset_index(drop=True).copy()
    out["pred"] = preds
    if proba is not None:
        out["pred_proba"] = proba
    return out


def main():
    parser = argparse.ArgumentParser(description="Load a model and predict on CSV/Parquet input")
    parser.add_argument("--model", required=True, help="Path to trained joblib model")
    parser.add_argument("--input", required=True, help="Path to input CSV/Parquet containing feature columns used in training")
    parser.add_argument("--out", required=False, help="Path to write predictions CSV")
    args = parser.parse_args()

    input_path = Path(args.input)
    if input_path.suffix in [".parquet", ".pq"]:
        df = pd.read_parquet(input_path)
    else:
        df = pd.read_csv(input_path)

    result = predict(df, Path(args.model))
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(args.out, index=False)
        logger.info("Saved predictions to %s", args.out)
    else:
        print(result.head(50).to_csv(index=False))


if __name__ == "__main__":
    main()
