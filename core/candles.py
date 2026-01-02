# core/candles.py

from datetime import datetime


class Candle:
    def init(self, timestamp, open_, high, low, close, volume):
        self.timestamp = timestamp
        self.time = datetime.fromtimestamp(timestamp / 1000)

        self.open = open_
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume

        # дополнительные поля (позже)
        self.oi = None
        self.oi_delta = None
        self.atr = None


class CandleFrame:
    def init(self, ohlcv, oi_series=None):
        self.candles = self._build(ohlcv, oi_series)

    def _build(self, ohlcv, oi_series):
        candles = []
        prev_oi = None

        for row in ohlcv:
            ts, o, h, l, c, v = row
            candle = Candle(ts, o, h, l, c, v)

            if oi_series and ts in oi_series:
                candle.oi = oi_series[ts]
                if prev_oi is not None:
                    candle.oi_delta = candle.oi - prev_oi
                prev_oi = candle.oi

            candles.append(candle)

        return candles

    def last_closed(self):
        # последняя ЗАКРЫТАЯ свеча
        return self.candles[-2]

    def recent(self, n=20):
        return self.candles[-n:]
