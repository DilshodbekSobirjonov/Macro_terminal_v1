# services/exchange.py

import requests
import time

BINANCE_FUTURES_URL = "https://fapi.binance.com"


class ExchangeService:
    def init(self):
        # Явно инициализируем
        self.base_url = BINANCE_FUTURES_URL

    def fetch_ohlcv(self, symbol, interval="30m", limit=200):
        """
        Fetch OHLCV candles from Binance Futures
        """
        url = BINANCE_FUTURES_URL + "/fapi/v1/klines"

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
                c[0],            # open time (ms)
                float(c[1]),     # open
                float(c[2]),     # high
                float(c[3]),     # low
                float(c[4]),     # close
                float(c[5])      # volume
            ])

        return candles

    def fetch_open_interest(self, symbol):
        url = BINANCE_FUTURES_URL + "/fapi/v1/openInterest"
        params = {"symbol": symbol.replace("/", "")}

        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()

        return float(r.json()["openInterest"])

    def now(self):
        return int(time.time() * 1000)
        def fetch_open_interest_history(self, symbol, interval="30m", limit=100):
    """
    Получает историю Open Interest с Binance Futures
    """
    url = BINANCE_FUTURES_URL + "/futures/data/openInterestHist"

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
