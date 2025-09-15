# backend/app/config.py
"""
Central configuration and pydantic models.

Design choices:
- Use pydantic for validation of config values (robust & explicit).
- Allow environment overrides for sensitive credentials.
"""
from pydantic import BaseSettings, Field, validator
from typing import Literal

class MT5Config(BaseSettings):
    server: str = Field(..., description="MT5 server name")
    login: int
    password: str
    use_mt5_terminal: bool = True

class RiskConfig(BaseSettings):
    max_risk_percent: float = 1.0
    default_risk_percent: float = 0.5
    max_open_trades: int = 6
    slippage_pips: float = 2.0

    @validator("max_risk_percent", "default_risk_percent")
    def bounds(cls, v):
        if v <= 0 or v > 100:
            raise ValueError("risk percent must be >0 and <=100")
        return v

class Settings(BaseSettings):
    env: Literal["dev", "staging", "prod"] = "dev"
    host: str = "0.0.0.0"
    port: int = 8000
    mt5: MT5Config
    risk: RiskConfig = RiskConfig()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()  # load from env / .env
