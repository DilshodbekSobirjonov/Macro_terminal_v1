# core/structure.py

from typing import List
from core.candles import Candle


class MarketStructure:
    def __init__(self, candles: List[Candle], lookback: int = 2):
        self.candles = candles
        self.lookback = lookback

        self.swing_highs = []
        self.swing_lows = []

        self._detect_swings()

    def _detect_swings(self):
        """
        Определяем swing highs / swing lows
        """
        for i in range(self.lookback, len(self.candles) - self.lookback):
            high = self.candles[i].high
            low = self.candles[i].low

            is_swing_high = True
            is_swing_low = True

            for j in range(1, self.lookback + 1):
                if high <= self.candles[i - j].high:
                    is_swing_high = False
                if high <= self.candles[i + j].high:
                    is_swing_high = False

                if low >= self.candles[i - j].low:
                    is_swing_low = False
                if low >= self.candles[i + j].low:
                    is_swing_low = False

            if is_swing_high:
                self.swing_highs.append((i, self.candles[i]))

            if is_swing_low:
                self.swing_lows.append((i, self.candles[i]))

    def last_swing_high(self):
        return self.swing_highs[-1] if self.swing_highs else None

    def last_swing_low(self):
        return self.swing_lows[-1] if self.swing_lows else None

    def detect_bos(self):
        """
        Break of Structure:
        цена пробивает последний swing high
        """
        last_high = self.last_swing_high()
        if not last_high:
            return False

        _, swing_candle = last_high
        current_price = self.candles[-1].close

        return current_price > swing_candle.high

    def detect_choch(self):
        """
        Change of Character:
        цена пробивает последний swing low
        """
        last_low = self.last_swing_low()
        if not last_low:
            return False

        _, swing_candle = last_low
        current_price = self.candles[-1].close

        return current_price < swing_candle.low
def detect_choch_bullish(candles):
    """
    Минимальный CHoCH:
    - было минимум 3 lower highs
    - текущий high > предыдущего lower high
    """
    if len(candles) < 6:
        return False

    highs = [c.high for c in candles[-6:-1]]

    # 3 подряд lower highs
    if not (highs[0] > highs[1] > highs[2]):
        return False

    # CHoCH: текущий high пробивает предыдущий lower high
    if candles[-1].high > highs[2]:
        return True

    return False