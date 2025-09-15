# backend/app/services/trade_executor.py

import os
import time
import logging
from pydantic import BaseModel, ValidationError

logger = logging.getLogger("TradeExecutor")

class TradeOrder(BaseModel):
    symbol: str
    direction: str  # 'buy' or 'sell'
    entry: float
    sl: float
    tp: float
    volume: float

class TradeExecutor:
    """Wrapper for MT5 or Broker API. Currently mocked."""

    def __init__(self):
        self.mt5_login = os.getenv("MT5_LOGIN")
        self.mt5_password = os.getenv("MT5_PASSWORD")
        self.mt5_server = os.getenv("MT5_SERVER")

    def execute(self, order: dict) -> dict:
        try:
            validated = TradeOrder(**order)
            logger.info(f"Executing trade: {validated.dict()}")

            # TODO: Replace with real MT5 or broker API call
            order_id = f"mock-{int(time.time())}"
            return {"status": "ok", "order_id": order_id, "symbol": validated.symbol}

        except ValidationError as ve:
            logger.error(f"Trade validation failed: {ve}")
            return {"status": "error", "message": "Invalid trade payload", "details": ve.errors()}

        except Exception as e:
            logger.error(f"Trade execution failed: {e}")
            return {"status": "error", "message": "Execution error"}
