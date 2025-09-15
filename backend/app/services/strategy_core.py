# backend/app/services/strategy_core.py

import logging
from typing import Dict, Union

import MetaTrader5 as mt5

from app.services.ml_optimizer import ml_optimizer
from app.services.market_data import get_atr
from app.services.signal_engine import Signal

logger = logging.getLogger("StrategyCore")


class StrategyCore:
    """Adaptive scalping logic with ML + ATR filtering."""

    def __init__(self, config: Dict = None):
        self.config = config or {
            "risk_pct": 0.005,             # % of balance risked per trade
            "min_atr_threshold": 0.0008,   # reject if volatility too low
            "symbol_defaults": {
                "EURUSD": {"multiplier": 1.0},
                "XAUUSD": {"multiplier": 10.0},
                "default": {"multiplier": 1.0},
            },
        }

    def _get_live_balance(self) -> float:
        """Fetch live balance from MT5 account."""
        acc_info = mt5.account_info()
        if acc_info is None:
            logger.warning("MT5 account_info() unavailable, fallback balance=1000.0")
            return 1000.0
        return float(acc_info.balance)

    async def evaluate(self, signal: Union[Signal, dict]) -> dict:
        """
        Evaluate a trading signal and return a structured decision.
        """
        # Normalize input
        if isinstance(signal, dict):
            symbol = signal.get("symbol", "default")
            confidence = signal.get("confidence", 0.5)
            direction = signal.get("direction", "buy")
        else:
            symbol = signal.symbol
            confidence = signal.confidence
            direction = signal.direction

        # Step 1: ML Optimization
        try:
            ml_result = await ml_optimizer.predict(signal)
        except Exception as e:
            logger.exception("ML optimizer failed: %s", e)
            return {"action": "reject", "reason": "ml_failure"}

        score = ml_result.get("score", confidence)
        sl_pips = ml_result.get("sl_pips", 10)
        tp_pips = ml_result.get("tp_pips", 8)

        if score < 0.55:
            logger.info("Rejected %s: low ML score (%.3f)", symbol, score)
            return {"action": "reject", "reason": "low_score", "score": score}

        # Step 2: ATR Volatility Filter
        try:
            atr = await get_atr(symbol, period=14)
        except Exception as e:
            logger.exception("ATR fetch failed: %s", e)
            return {"action": "reject", "reason": "atr_failure"}

        if atr < self.config["min_atr_threshold"]:
            logger.info("Rejected %s: low ATR (%.5f)", symbol, atr)
            return {"action": "reject", "reason": "low_volatility", "atr": atr}

        # Step 3: Position Sizing (live balance-aware)
        balance = self._get_live_balance()     # <-- pulls actual Exness account balance
        risk_pct = self.config["risk_pct"]
        multiplier = self.config["symbol_defaults"].get(
            symbol, self.config["symbol_defaults"]["default"]
        )["multiplier"]

        lot = max(0.01, (balance * risk_pct) / max(1.0, sl_pips * multiplier))

        decision = {
            "action": "accept",
            "symbol": symbol,
            "direction": direction,
            "lot": round(lot, 2),
            "sl_pips": sl_pips,
            "tp_pips": tp_pips,
            "score": round(score, 3),
            "atr": round(atr, 5),
            "balance": round(balance, 2),
        }

        logger.info("Accepted %s: %s", symbol, decision)
        return decision
