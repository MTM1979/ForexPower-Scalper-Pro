# backend/app/services/signal_engine.py

import asyncio
import logging
import random
from datetime import datetime

logger = logging.getLogger("SignalEngine")

class SignalEngine:
    """Generates and streams trading signals. Emits executed trades."""

    def __init__(self):
        self._signal_queue = asyncio.Queue()
        self._trade_queue = asyncio.Queue()
        self._running = False

    def get_recent_signals(self) -> list:
        # Placeholder: return last few signals
        return [
            {"symbol": "EURUSD", "confidence": 0.72, "timestamp": datetime.utcnow().timestamp()},
            {"symbol": "XAUUSD", "confidence": 0.65, "timestamp": datetime.utcnow().timestamp()}
        ]

    def start(self, loop):
        if not self._running:
            loop.create_task(self._generate_signals())
            self._running = True
            logger.info("SignalEngine started.")

    async def _generate_signals(self):
        while True:
            await asyncio.sleep(5)  # Simulate signal generation
            signal = {
                "symbol": random.choice(["EURUSD", "XAUUSD"]),
                "confidence": round(random.uniform(0.5, 0.9), 2),
                "timestamp": datetime.utcnow().timestamp()
            }
            await self._signal_queue.put(signal)
            logger.info(f"New signal generated: {signal}")

            # Simulate trade execution and emit trade
            trade = {
                "symbol": signal["symbol"],
                "direction": "buy",
                "volume": 0.1,
                "profit": round(random.uniform(-5, 15), 2),
                "timestamp": signal["timestamp"]
            }
            await self._trade_queue.put(trade)
            logger.info(f"Trade executed: {trade}")

    async def stream(self):
        while True:
            signal = await self._signal_queue.get()
            yield signal

    async def trade_stream(self):
        while True:
            trade = await self._trade_queue.get()
            yield trade

# Singleton instance
signal_engine = SignalEngine()

def get_signal_engine():
    return signal_engine
