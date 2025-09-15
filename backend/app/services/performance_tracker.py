# backend/app/services/performance_tracker.py

import logging
from datetime import datetime

logger = logging.getLogger("PerformanceTracker")

class PerformanceTracker:
    def __init__(self):
        self.trades = []

    def record(self, trade: dict):
        trade_record = {
            "symbol": trade.get("symbol"),
            "timestamp": trade.get("timestamp", datetime.utcnow().timestamp()),
            "profit": trade.get("profit", 0.0),
            "direction": trade.get("direction"),
            "volume": trade.get("volume", 0.0)
        }
        self.trades.append(trade_record)
        logger.info(f"Trade recorded: {trade_record}")

    def summary(self) -> dict:
        total = len(self.trades)
        wins = sum(1 for t in self.trades if t["profit"] > 0)
        losses = total - wins
        net_profit = sum(t["profit"] for t in self.trades)
        win_rate = round((wins / total) * 100, 2) if total > 0 else 0.0

        return {
            "total_trades": total,
            "wins": wins,
            "losses": losses,
            "win_rate_percent": win_rate,
            "net_profit": round(net_profit, 2)
        }
