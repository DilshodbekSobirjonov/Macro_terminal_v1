# services/exchange.py

import requests
import time

BINANCE_FUTURES_URL = "https://fapi.binance.com"


class ExchangeService:
    def __init__(self):
        self.base_url = BINANCE_FUTURES_URL

    def fetch_ohlcv(self, symbol, interval="30m", limit=200):
        """
        Получает OHLCV свечи с Binance Futures
        """
        url = self.base_url + "/fapi/v1/klines"

        params = {
            "symbol": symbol.replace("/", ""),
            "interval": interval,
            "limit": limit
        }

        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()

        data = r.json()

        candles = []
        for c in data:
            candles.append([
                int(c[0]),        # open time (ms)
                float(c[1]),      # open
                float(c[2]),      # high
                float(c[3]),      # low
                float(c[4]),      # close
                float(c[5])       # volume
            ])

        return candles

    def fetch_open_interest_history(self, symbol, interval="30m", limit=200):
        """
        Получает историю Open Interest (по таймфрейму)
        """
        url = self.base_url + "/futures/data/openInterestHist"

        params = {
            "symbol": symbol.replace("/", ""),
            "period": interval,
            "limit": limit
        }

        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()

        data = r.json()

        oi_series = {}
        for item in data:
            oi_series[int(item["timestamp"])] = float(item["sumOpenInterest"])

        return oi_series

    def now(self):
        return int(time.time() * 1000)
