# backend/app/api/routes.py

from fastapi import APIRouter, Depends, HTTPException
from app.services.signal_engine import signal_engine
from app.services.trade_executor import trade_executor
from app.services.performance_tracker import performance_tracker
from app.models.trade import TradePayload, TradeResponse
import logging

router = APIRouter()
logger = logging.getLogger("ForexPowerScalperPro")

@router.get("/signals", response_model=list[dict])
async def get_signals():
    try:
        signals = signal_engine.get_recent_signals()
        logger.info(f"Fetched {len(signals)} signals")
        return signals
    except Exception as e:
        logger.error(f"Signal fetch failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch signals")

@router.post("/trade/execute", response_model=TradeResponse)
async def execute_trade(payload: TradePayload):
    try:
        result = trade_executor.execute(payload.model_dump())
        logger.info(f"Trade executed: {result}")
        return result
    except Exception as e:
        logger.error(f"Trade execution failed: {e}")
        raise HTTPException(status_code=500, detail="Trade execution error")

@router.get("/metrics", response_model=dict)
async def metrics():
    try:
        summary = performance_tracker.summary()
        logger.info("Metrics summary retrieved")
        return summary
    except Exception as e:
        logger.error(f"Metrics fetch failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")
