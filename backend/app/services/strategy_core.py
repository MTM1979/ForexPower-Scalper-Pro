# backend/app/services/strategy_core.py

import logging
from app.services.ml_optimizer import ml_optimizer
from app.services.market_data import get_atr

logger = logging.getLogger("StrategyCore")

class StrategyCore:
    """Adaptive scalping logic with ML and ATR filtering."""

    def __init__(self, config=None):
        self.config = config or {
            "risk_pct": 0.005,
            "default_balance": 1000.0,
            "min_atr_threshold": 0.0008,  # e.g. 0.08% volatility
            "symbol_defaults": {
                "EURUSD": {"multiplier": 1.0},
                "XAUUSD": {"multiplier": 10.0},
                "default": {"multiplier": 1.0}
            }
        }

    async def evaluate(self, signal: dict) -> dict:
        symbol = signal.get("symbol", "default")
        conf = signal.get("confidence", 0.5)

        # Get ML prediction
        ml_result = await ml_optimizer.predict(signal)
        score = ml_result.get("score", conf)
        sl_pips = ml_result.get("sl_pips", 10)
        tp_pips = ml_result.get("tp_pips", 8)

        if score < 0.55:
            logger.info(f"Rejected: low ML score ({score})")
            return {"action": "reject", "reason": "low_score", "score": score}

        # Get ATR for volatility filtering
        atr = await get_atr(symbol, period=14)
        if atr < self.config["min_atr_threshold"]:
            logger.info(f"Rejected: low ATR ({atr})")
            return {"action": "reject", "reason": "low_volatility", "atr": atr}

        # Position sizing
        balance = self.config["default_balance"]
        risk_pct = self.config["risk_pct"]
        multiplier = self.config["symbol_defaults"].get(symbol, self.config["symbol_defaults"]["default"])["multiplier"]
        lot = max(0.01, (balance * risk_pct) / (sl_pips * multiplier))

        logger.info(f"Accepted: {symbol}, lot={lot}, SL={sl_pips}, TP={tp_pips}, ATR={atr}")
        return {
            "action": "accept",
            "symbol": symbol,
            "lot": round(lot, 2),
            "sl_pips": sl_pips,
            "tp_pips": tp_pips,
            "score": round(score, 3),
            "atr": round(atr, 5)
        }
