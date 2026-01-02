# core/candles.py

import pandas as pd
from datetime import datetime


class CandleFrame:
    def __init__(self, ohlcv, oi_series=None):
        """
        ohlcv: list from ccxt
        oi_series: dict {timestamp: oi}
        """
        self.df = self._build_dataframe(ohlcv, oi_series)

    def _build_dataframe(self, ohlcv, oi_series):
        df = pd.DataFrame(
            ohlcv,
            columns=[
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume"
            ]
        )

        df["time"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("time", inplace=True)

        # OI delta
        if oi_series:
            df["oi"] = df["timestamp"].map(oi_series)
            df["oi_delta"] = df["oi"].diff()
        else:
            df["oi"] = None
            df["oi_delta"] = None

        return df

    def last_closed(self):
        """
        Возвращает последнюю ЗАКРЫТУЮ свечу
        """
        return self.df.iloc[-2]

    def recent(self, n=20):
        return self.df.tail(n)
