# ml/data_prep/dataset_builder.py
from __future__ import annotations
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Iterable, Optional, Tuple
import logging
from .features import add_standard_features

logger = logging.getLogger("ml.dataset_builder")
logger.addHandler(logging.NullHandler())


class DatasetBuilder:
    """
    Builds ML-ready datasets from OHLCV candle data.

    Usage:
        builder = DatasetBuilder(horizon=10, pip_size=0.0001, threshold_pips=1.0)
        df = builder.load_csv("data/EURUSD_1m.csv")
        dataset = builder.build(df)
        builder.save(dataset, "data/train.parquet")
    """

    def __init__(
        self,
        horizon: int = 10,
        pip_size: float = 0.0001,
        threshold_pips: float = 0.0,
        feature_kwargs: Optional[dict] = None,
    ) -> None:
        """
        Args:
            horizon: lookahead bars to determine label.
            pip_size: pip value (0.0001 for most pairs, 0.01 for JPY pairs).
            threshold_pips: minimum pip move to label as directional move; 0 for any move.
            feature_kwargs: passed to feature builder.
        """
        if horizon <= 0:
            raise ValueError("horizon must be > 0")
        self.horizon = horizon
        self.pip_size = pip_size
        self.threshold_pips = float(threshold_pips)
        self.feature_kwargs = feature_kwargs or {}
        logger.debug("DatasetBuilder initialized: horizon=%s pip_size=%s threshold_pips=%s", horizon, pip_size, threshold_pips)

    def load_csv(self, path: str | Path, timestamp_col: Optional[str] = "timestamp") -> pd.DataFrame:
        """Load CSV to DataFrame and validate columns."""
        df = pd.read_csv(path)
        if timestamp_col in df.columns:
            try:
                df[timestamp_col] = pd.to_datetime(df[timestamp_col])
            except Exception:
                logger.debug("timestamp parsing failed, leaving as-is")
        expected = {"open", "high", "low", "close", "volume"}
        if not expected.issubset(df.columns):
            raise ValueError(f"CSV missing required columns: {expected - set(df.columns)}")
        # Ensure sorted by time ascending
        if timestamp_col in df.columns:
            df = df.sort_values(timestamp_col).reset_index(drop=True)
        return df

    def _label_directional(self, df: pd.DataFrame) -> pd.Series:
        """
        Create a binary label: 1 if close price moves up by threshold within horizon,
        -1 if moves down by threshold within horizon, else 0 (no significant move).
        For classification we'll convert to 0/1 (up vs not-up) or multi-class optionally.
        """
        close = df["close"].values
        n = len(close)
        labels = np.zeros(n, dtype=np.int8)

        # compute future close at horizon (shift -horizon)
        future = np.roll(close, -self.horizon)
        # last horizon values are invalid
        future[-self.horizon:] = np.nan

        move = (future - close) / self.pip_size  # number of pips
        up_mask = move >= self.threshold_pips
        down_mask = move <= -self.threshold_pips

        labels[up_mask] = 1
        labels[down_mask] = -1
        labels = pd.Series(labels, index=df.index)
        return labels

    def build(
        self,
        raw_df: pd.DataFrame,
        drop_zeros: bool = True,
        keep_multiclass: bool = False,
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Build features and labels.

        Returns:
            X: DataFrame of features (aligned), y: Series of labels.
        """
        df = raw_df.copy()
        df = add_standard_features(df, forward_returns=self.horizon, **self.feature_kwargs)
        labels = self._label_directional(df)

        # Align features and labels: drop last horizon rows with NaN future
        valid_idx = labels.index[~labels.isna()]
        X = df.loc[valid_idx].copy()
        y = labels.loc[valid_idx].copy()

        # Convert multiclass to binary if requested (1 -> 1, others -> 0)
        if not keep_multiclass:
            y_binary = (y == 1).astype(np.int8)
            y = y_binary

        if drop_zeros:
            # Optionally drop neutral rows (if multiclass) or keep all for binary
            if keep_multiclass:
                mask = y != 0
                X = X.loc[mask]
                y = y.loc[mask]
            # for binary, no drop needed (0 means not-up)
        # Drop columns that leak the future (e.g., future_return_* or anything with "future")
        leak_cols = [c for c in X.columns if "future" in str(c).lower()]
        if leak_cols:
            X = X.drop(columns=leak_cols)

        # Final cleanup: replace infinities and NaNs
        X = X.replace([np.inf, -np.inf], np.nan).fillna(method="ffill").fillna(method="bfill").fillna(0.0)
        y = y.fillna(0).astype(int)

        logger.info("Built dataset: X=%s y=%s", X.shape, y.shape)
        return X, y

    def save(self, X: pd.DataFrame, y: pd.Series, path: str | Path) -> None:
        """Save dataset to disk (parquet by default if extension supports it)."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.suffix in [".parquet", ".pq"]:
            df = X.copy()
            df["__label__"] = y.values
            df.to_parquet(p, index=False)
        else:
            # default to CSV
            df = X.copy()
            df["__label__"] = y.values
            df.to_csv(p, index=False)
        logger.info("Saved dataset to %s", p.resolve())
