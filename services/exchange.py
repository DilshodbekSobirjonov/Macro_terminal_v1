# services/exchange.py

import requests
import time


class ExchangeService:
    def __init__(self):
        # Binance Futures API
        self.base_url = "https://fapi.binance.com"

    # --------------------------------------------------
    # OHLCV (candles)
    # --------------------------------------------------
    def fetch_ohlcv(self, symbol, timeframe, limit=200):
        url = f"{self.base_url}/fapi/v1/klines"

        params = {
            "symbol": symbol,
            "interval": timeframe,
            "limit": limit
        }

        try:
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
        except requests.RequestException:
            return []

        data = r.json()

        candles = []
        for c in data:
            candles.append([
                int(c[0]),          # timestamp
                float(c[1]),        # open
                float(c[2]),        # high
                float(c[3]),        # low
                float(c[4]),        # close
                float(c[5])         # volume
            ])

        return candles

    # --------------------------------------------------
    # OPEN INTEREST HISTORY
    # --------------------------------------------------
    def fetch_open_interest_history(self, symbol, timeframe, limit=200):
        """
        Binance даёт OI по времени, но не по интервалу свечи,
        поэтому мы просто мапим timestamp -> OI
        """
        url = f"{self.base_url}/futures/data/openInterestHist"

        params = {
            "symbol": symbol,
            "period": timeframe,
            "limit": limit
        }

        try:
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
        except requests.RequestException:
            return {}

        data = r.json()
        oi_series = {}

        for item in data:
            try:
                ts = int(item["timestamp"])
                oi = float(item["sumOpenInterest"])
                oi_series[ts] = oi
            except (KeyError, TypeError, ValueError):
                continue

        return oi_series

    # --------------------------------------------------
    # 24H TICKERS (for dynamic universe)
    # --------------------------------------------------
    def fetch_tickers(self):
        url = f"{self.base_url}/fapi/v1/ticker/24hr"

        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
        except requests.RequestException:
            return {}

        data = r.json()
        tickers = {}

        for item in data:
            symbol = item.get("symbol")
            if not symbol:
                continue

            try:
                tickers[symbol] = {
                    "quoteVolume": float(item.get("quoteVolume", 0)),
                    "high": float(item.get("highPrice", 0)),
                    "low": float(item.get("lowPrice", 0)),
                    "last": float(item.get("lastPrice", 0)),
                }
            except (TypeError, ValueError):
                continue

        return tickers