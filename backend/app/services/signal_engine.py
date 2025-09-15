# backend/app/services/signal_engine.py
"""
Signal Engine
-------------
Generates candidate trading signals from market data.

Design choices:
- Stateless analysis functions for testability.
- Async queues maintained for dashboard streaming compatibility.
- Easy integration with strategy_core, ml_optimizer, and trade_executor.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict
import numpy as np

logger = logging.getLogger("SignalEngine")


@dataclass
class MarketBar:
    symbol: str
    timeframe: str
    ts: int
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None


@dataclass
class Signal:
    symbol: str
    direction: str  # "buy" | "sell"
    reason: str
    stop_loss: float
    take_profit: Optional[float]
    confidence: float
    timestamp: float


class SignalEngine:
    """Generates signals and streams them asynchronously."""

    def __init__(self):
        self._signal_queue = asyncio.Queue()
        self._trade_queue = asyncio.Queue()
        self._running = False

    # ---------------- Strategy logic ---------------- #
    def compute_sma(self, series: List[float], period: int) -> float:
        if len(series) < period:
            raise ValueError("Series too short for SMA")
        return float(np.mean(series[-period:]))

    def simple_momentum_signal(self, bars: List[MarketBar]) -> Optional[Signal]:
        """Example: SMA momentum crossover strategy."""
        if len(bars) < 50:
            return None

        closes = [b.close for b in bars]
        short = self.compute_sma(closes, 3)
        long = self.compute_sma(closes, 21)
        latest = closes[-1]

        confidence = min(1.0, abs(short - long) / max(1e-6, long) * 10.0)

        if short > long and latest > short:
            sl = min(bars[-1].low, bars[-2].low)
            tp = latest + (latest - sl) * 1.5
            return Signal(
                symbol=bars[-1].symbol,
                direction="buy",
                reason="sma_momentum",
                stop_loss=sl,
                take_profit=tp,
                confidence=confidence,
                timestamp=datetime.utcnow().timestamp(),
            )

        if short < long and latest < short:
            sl = max(bars[-1].high, bars[-2].high)
            tp = latest - (sl - latest) * 1.5
            return Signal(
                symbol=bars[-1].symbol,
                direction="sell",
                reason="sma_momentum",
                stop_loss=sl,
                take_profit=tp,
                confidence=confidence,
                timestamp=datetime.utcnow().timestamp(),
            )

        return None

    # ---------------- Async streaming ---------------- #
    def start(self, loop, data_feed):
        """
        Start background signal generation.
        `data_feed`: async function yielding (symbol, List[MarketBar]).
        """
        if not self._running:
            loop.create_task(self._run(data_feed))
            self._running = True
            logger.info("SignalEngine started.")

    async def _run(self, data_feed):
        """Continuously fetch bars from data_feed and generate signals."""
        async for symbol, bars in data_feed():
            try:
                sig = self.simple_momentum_signal(bars)
                if sig:
                    await self._signal_queue.put(sig.__dict__)
                    logger.info("New signal generated: %s", sig)

                    # Placeholder trade execution event (for dashboard demo)
                    trade = {
                        "symbol": sig.symbol,
                        "direction": sig.direction,
                        "volume": 0.1,
                        "profit": 0.0,
                        "timestamp": sig.timestamp,
                    }
                    await self._trade_queue.put(trade)
            except Exception as e:
                logger.exception("Signal generation failed for %s: %s", symbol, e)

    async def stream(self):
        """Async generator yielding signals (dicts)."""
        while True:
            sig = await self._signal_queue.get()
            yield sig

    async def trade_stream(self):
        """Async generator yielding trades (dicts)."""
        while True:
            trade = await self._trade_queue.get()
            yield trade

    # ---------------- Helper ---------------- #
    def get_recent_signals(self) -> List[Dict]:
        """Non-blocking snapshot for quick dashboard polling."""
        return list(self._signal_queue._queue)[-5:]


# Singleton instance
signal_engine = SignalEngine()


def get_signal_engine():
    return signal_engine
