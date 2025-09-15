# backend/app/workers/worker.py

import asyncio
from app.services.signal_engine import get_signal_engine
from app.services.performance_tracker import performance_tracker

def start_background_workers(signal_engine=None):
    loop = asyncio.get_event_loop()
    if signal_engine is None:
        signal_engine = get_signal_engine()

    # Start signal engine
    signal_engine.start(loop)

    # Example: Hook into signal_engine to record trades
    async def trade_listener():
        async for trade in signal_engine.trade_stream():
            performance_tracker.record(trade)

    loop.create_task(trade_listener())
