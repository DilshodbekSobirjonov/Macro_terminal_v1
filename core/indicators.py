# core/indicators.py

from typing import List
from core.candles import Candle


def calculate_atr(candles: List[Candle], period: int = 14):
    """
    Рассчитывает ATR для последней свечи
    """
    if len(candles) < period + 1:
        return None

    trs = []

    for i in range(-period, 0):
        current = candles[i]
        previous = candles[i - 1]

        tr = max(
            current.high - current.low,
            abs(current.high - previous.close),
            abs(current.low - previous.close)
        )
        trs.append(tr)

    return sum(trs) / period


def atr_regime(candles: List[Candle], lookback: int = 20):
    """
    Определяет режим ATR:
    - compression
    - expansion
    - overheated
    """
    if len(candles) < lookback + 20:
        return None

    atr_values = []

    for i in range(-lookback, 0):
        atr = calculate_atr(candles[:i])
        if atr:
            atr_values.append(atr)

    if not atr_values:
        return None

    current_atr = atr_values[-1]
    avg_atr = sum(atr_values) / len(atr_values)

    if current_atr < avg_atr * 0.8:
        return "compression"

    if avg_atr * 0.8 <= current_atr <= avg_atr * 1.8:
        return "expansion"

    return "overheated"
