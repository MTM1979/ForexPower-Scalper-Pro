# ml/data_prep/features.py
from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Iterable, Optional
import logging

logger = logging.getLogger("ml.features")
logger.addHandler(logging.NullHandler())


def _ewm(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def sma(series: pd.Series, window: int) -> pd.Series:
    """Simple moving average."""
    return series.rolling(window=window, min_periods=1).mean()


def ema(series: pd.Series, span: int) -> pd.Series:
    """Exponential moving average (span parameter)."""
    return _ewm(series, span=span)


def rolling_std(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=1).std(ddof=0)


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index (vectorized)."""
    delta = close.diff()
    up = delta.clip(lower=0.0)
    down = -1.0 * delta.clip(upper=0.0)

    # exponential / Wilder smoothing
    ma_up = up.ewm(alpha=1.0/period, adjust=False).mean()
    ma_down = down.ewm(alpha=1.0/period, adjust=False).mean()

    rs = ma_up / (ma_down.replace(0, np.nan))
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.fillna(50.0)
    return rsi


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average True Range (ATR) implemented with Wilder smoothing."""
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr_series = tr.ewm(alpha=1.0/period, adjust=False).mean()
    return atr_series


def pct_change(close: pd.Series, periods: int = 1) -> pd.Series:
    return close.pct_change(periods=periods).fillna(0.0)


def log_return(close: pd.Series, periods: int = 1) -> pd.Series:
    return np.log(close).diff(periods=periods).fillna(0.0)


def rolling_skew(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=1).skew().fillna(0.0)


def rolling_kurt(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=1).kurt().fillna(0.0)


def add_standard_features(
    df: pd.DataFrame,
    short_windows: Iterable[int] = (5, 10),
    long_windows: Iterable[int] = (20, 50),
    atr_period: int = 14,
    rsi_period: int = 14,
    forward_returns: Optional[int] = None,
) -> pd.DataFrame:
    """
    Add a standard set of features to an OHLCV DataFrame.

    Expects columns: ['open','high','low','close','volume'] and optionally 'timestamp'.
    Returns a new DataFrame with feature columns appended.
    """
    df = df.copy()
    required = {"open", "high", "low", "close", "volume"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(f"Missing required columns: {missing}")

    close = df["close"]
    high = df["high"]
    low = df["low"]
    vol = df["volume"]

    # Moving averages
    for w in set(short_windows) | set(long_windows):
        df[f"sma_{w}"] = sma(close, w)
        df[f"ema_{w}"] = ema(close, w)

    # Price derivatives
    df["return_1"] = pct_change(close, 1)
    df["log_return_1"] = log_return(close, 1)

    # Volatility
    df["roll_std_10"] = rolling_std(df["log_return_1"], 10)
    df["roll_std_20"] = rolling_std(df["log_return_1"], 20)

    # Momentum / Strength
    df[f"rsi_{rsi_period}"] = rsi(close, period=rsi_period)

    # ATR / volatility measure
    df[f"atr_{atr_period}"] = atr(high, low, close, period=atr_period)

    # Skew / kurtosis
    df["skew_20"] = rolling_skew(df["log_return_1"], 20)
    df["kurt_20"] = rolling_kurt(df["log_return_1"], 20)

    # Rolling volumes
    df["vol_ma_10"] = vol.rolling(window=10, min_periods=1).mean()
    df["vol_ma_20"] = vol.rolling(window=20, min_periods=1).mean()

    # Spread features if available
    if "bid" in df.columns and "ask" in df.columns:
        df["spread"] = (df["ask"] - df["bid"]).abs()
        df["spread_ma_10"] = df["spread"].rolling(window=10, min_periods=1).mean()

    # Forward returns (optional)
    if forward_returns and forward_returns > 0:
        df[f"future_return_{forward_returns}"] = pct_change(close, -forward_returns)

    # Drop rows with NA if any remain, but keep index alignment
    df = df.replace([np.inf, -np.inf], np.nan).fillna(method="ffill").fillna(method="bfill").fillna(0.0)
    return df
