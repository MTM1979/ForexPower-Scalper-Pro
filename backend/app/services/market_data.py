# backend/app/services/market_data.py

import random

async def get_atr(symbol: str, period: int = 14) -> float:
    # Replace with real MT5 or broker API call
    simulated_atr = random.uniform(0.0005, 0.0015)
    return simulated_atr
