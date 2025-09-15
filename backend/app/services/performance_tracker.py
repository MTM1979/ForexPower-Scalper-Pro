from app.database import SessionLocal, Trade

class PerformanceTracker:
    def __init__(self):
        self.db = SessionLocal()

    def record(self, trade: dict):
        new_trade = Trade(**trade)
        self.db.add(new_trade)
        self.db.commit()

    def summary(self):
        trades = self.db.query(Trade).all()
        wins = sum(1 for t in trades if t.profit > 0)
        total = len(trades)
        net_profit = sum(t.profit for t in trades)
        return {
            "total_trades": total,
            "wins": wins,
            "net_profit": round(net_profit, 2)
        }
