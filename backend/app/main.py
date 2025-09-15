# backend/app/main.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest
from app.api.routes import router as api_router
from app.services.signal_engine import SignalEngine
from app.workers.worker import start_background_workers
import asyncio
import logging
import redis.asyncio as redis

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ForexPowerScalperPro")

# Redis setup
redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)
REDIS_CHANNEL = "signal_stream"

# Prometheus metrics
signal_counter = Counter("signals_processed_total", "Total signals processed")
signal_latency = Histogram("signal_latency_seconds", "Latency of signal processing")

# FastAPI app
app = FastAPI(title="ForexPowerScalperPro API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

# Singleton signal engine
signal_engine = SignalEngine()

@app.on_event("startup")
async def on_startup():
    logger.info("Starting background workers...")
    asyncio.create_task(start_background_workers(signal_engine))
    logger.info("ForexPowerScalperPro backend is live.")

@app.get("/health")
async def health():
    return {"status": "ok", "uptime": "running"}

@app.get("/metrics")
async def metrics():
    return generate_latest()

@app.websocket("/ws/stream")
async def ws_stream(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection accepted.")

    try:
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(REDIS_CHANNEL)

        async for message in pubsub.listen():
            if message["type"] == "message":
                signal_counter.inc()
                with signal_latency.time():
                    await websocket.send_json(message["data"])
                    await asyncio.sleep(0.05)  # Throttle to avoid flooding
    except WebSocketDisconnect:
        logger.warning("WebSocket disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()
