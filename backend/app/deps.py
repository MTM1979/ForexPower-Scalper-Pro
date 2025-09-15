# backend/app/deps.py

from fastapi import Depends, Header, HTTPException
from app.services.performance_tracker import performance_tracker
from app.services.signal_engine import signal_engine
from app.services.trade_executor import trade_executor
import jwt
import os

SECRET_KEY = os.getenv("JWT_SECRET", "forexsecret")

def get_tracker():
    return performance_tracker

def get_executor():
    return trade_executor

def get_signal_engine():
    return signal_engine

def validate_token(token: str = Header(...)):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=403, detail="Invalid token")
