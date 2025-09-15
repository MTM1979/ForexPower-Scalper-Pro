from fastapi import APIRouter, Depends, HTTPException
from app.deps import (
    validate_token,
    get_executor,
    get_tracker,
    get_signal_engine
)
from app.models.trade import TradePayload, TradeResponse
from app.api.auth import router as auth_router
from app.services.ml_optimizer import ml_optimizer
import logging

router = APIRouter()
logger = logging.getLogger("ForexPowerScalperPro")

# Include authentication routes
router.include_router(auth_router, prefix="/auth")

@router.get("/signals", response_model=list[dict])
async def get_signals(signal_engine=Depends(get_signal_engine)):
    try:
        signals = signal_engine.get_recent_signals()
        logger.info(f"Fetched {len(signals)} signals")
        return signals
    except Exception as e:
        logger.error(f"Signal fetch failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch signals")

@router.post("/trade/execute", response_model=TradeResponse)
async def execute_trade(
    payload: TradePayload,
    user=Depends(validate_token),
    executor=Depends(get_executor)
):
    try:
        result = executor.execute(payload.model_dump())
        logger.info(f"Trade executed by {user['sub']}: {result}")
        return result
    except Exception as e:
        logger.error(f"Trade execution failed: {e}")
        raise HTTPException(status_code=500, detail="Trade execution error")

@router.get("/metrics", response_model=dict)
async def metrics(tracker=Depends(get_tracker)):
    try:
        summary = tracker.summary()
        logger.info("Metrics summary retrieved")
        return summary
    except Exception as e:
        logger.error(f"Metrics fetch failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")

@router.post("/ml/predict", response_model=dict)
async def ml_predict(signal: dict):
    try:
        result = await ml_optimizer.predict(signal)
        logger.info(f"ML prediction returned: {result}")
        return result
    except Exception as e:
        logger.error(f"ML prediction failed: {e}")
        raise HTTPException(status_code=500, detail="ML prediction error")
