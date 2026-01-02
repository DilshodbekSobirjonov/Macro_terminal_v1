# services/exchange.py

import ccxt
import time


class ExchangeService:
    def __init__(self, name="binance"):
        if name == "binance":
            self.exchange = ccxt.binance({
                "enableRateLimit": True,
                "options": {
                    "defaultType": "future"  # для OI
                }
            })
        else:
            raise ValueError("Exchange not supported")

    def fetch_ohlcv(self, symbol, timeframe, limit=200):
        """
        Возвращает OHLCV свечи
        """
        return self.exchange.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit
        )

    def fetch_open_interest(self, symbol):
        """
        Возвращает текущее Open Interest
        """
        try:
            oi = self.exchange.fetch_open_interest(symbol)
            return oi["openInterest"]
        except Exception:
            return None

    def now(self):
        return int(time.time() * 1000)
