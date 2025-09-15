# backend/app/services/trade_executor.py
"""
Trade Executor
--------------
Places trades with Exness MT5 broker based on validated signals.
"""

import logging
from datetime import datetime
import MetaTrader5 as mt5

logger = logging.getLogger("TradeExecutor")


class TradeExecutor:
    """Handles trade execution via MetaTrader5."""

    def __init__(self, config=None):
        self.config = config or {
            "login": 161282252,
            "password": "YOUR_PASSWORD",       # TODO: Secure via env var / secrets manager
            "server": "Exness-MT5Real21",
        }
        self.connected = False

    # ---------------- MT5 Session ---------------- #
    def connect(self):
        """Initialize MT5 connection."""
        if not mt5.initialize():
            raise RuntimeError("Failed to initialize MT5")

        authorized = mt5.login(
            login=self.config["login"],
            password=self.config["password"],
            server=self.config["server"],
        )
        if not authorized:
            raise RuntimeError(f"MT5 login failed: {mt5.last_error()}")
        self.connected = True
        logger.info("Connected to MT5 account %s", self.config["login"])

    def shutdown(self):
        mt5.shutdown()
        self.connected = False
        logger.info("Disconnected from MT5")

    # ---------------- Trade Execution ---------------- #
    def place_trade(self, decision: dict):
        """
        Execute trade based on decision dict from StrategyCore.
        Example decision:
        {
            "action": "accept",
            "symbol": "EURUSD",
            "lot": 0.05,
            "sl_pips": 10,
            "tp_pips": 15,
            "score": 0.72,
            "atr": 0.0012
        }
        """
        if decision.get("action") != "accept":
            logger.info("Decision rejected, skipping execution: %s", decision)
            return None

        symbol = decision["symbol"]
        lot = decision["lot"]
        sl_pips = decision["sl_pips"]
        tp_pips = decision["tp_pips"]

        # Ensure MT5 connected
        if not self.connected:
            self.connect()

        # Get symbol info
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            raise RuntimeError(f"Symbol {symbol} not found")
        if not symbol_info.visible:
            mt5.symbol_select(symbol, True)

        # Current price
        price = mt5.symbol_info_tick(symbol)
        if not price:
            raise RuntimeError(f"Failed to fetch price for {symbol}")

        # Direction
        order_type = mt5.ORDER_BUY if decision.get("direction", "buy") == "buy" else mt5.ORDER_SELL
        entry_price = price.ask if order_type == mt5.ORDER_BUY else price.bid

        # SL & TP in price terms (convert from pips)
        point = symbol_info.point
        sl = entry_price - sl_pips * point if order_type == mt5.ORDER_BUY else entry_price + sl_pips * point
        tp = entry_price + tp_pips * point if order_type == mt5.ORDER_BUY else entry_price - tp_pips * point

        # Order request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": order_type,
            "price": entry_price,
            "sl": round(sl, symbol_info.digits),
            "tp": round(tp, symbol_info.digits),
            "deviation": 10,
            "magic": 1001,
            "comment": f"ScalperPro {decision.get('reason', 'strategy')}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        logger.info("Placing order: %s", request)

        # Send order
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error("Order failed: %s", result)
            return None

        logger.info("Order successful: %s", result)
        return result


# Singleton instance
trade_executor = TradeExecutor()


def get_trade_executor():
    return trade_executor
