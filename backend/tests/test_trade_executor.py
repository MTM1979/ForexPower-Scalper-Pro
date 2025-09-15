from app.services.trade_executor import trade_executor

def test_execute_trade():
    order = {
        "symbol": "EURUSD",
        "direction": "buy",
        "entry": 1.1234,
        "sl": 1.1200,
        "tp": 1.1300,
        "volume": 0.1
    }
    result = trade_executor.execute(order)
    assert result["status"] == "ok"
