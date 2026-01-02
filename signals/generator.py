# signals/generator.py

from services.exchange import ExchangeService
from core.candles import CandleFrame
from core.structure import MarketStructure
from core.indicators import (
    calculate_atr,
    atr_regime,
    volume_anomaly,
    oi_delta_positive
)

exchange = ExchangeService()
TIMEFRAME = "30m"


def generate_signal(symbol):
    """
    IMPULSE DETECTOR
    Использует РЕАЛЬНУЮ структуру проекта
    """
    ohlcv = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=200)
    oi = exchange.fetch_open_interest_history(symbol, TIMEFRAME, limit=200)

    if not ohlcv:
        return None

    candles = CandleFrame(ohlcv, oi)
    structure = MarketStructure(candles.candles)

    # 1️⃣ BOS (реальный, из твоего кода)
    if not structure.detect_bos():
        return None

    # 2️⃣ ATR regime — только expansion
    if atr_regime(candles.candles) != "expansion":
        return None

    # 3️⃣ Volume anomaly
    if not volume_anomaly(candles.candles, multiplier=1.5):
        return None

    # 4️⃣ OI direction
    if not oi_delta_positive(candles.candles):
        return None

    # 5️⃣ ATR value
    atr = calculate_atr(candles.candles)
    if atr is None:
        return None

    last = candles.candles[-1]

    return {
        "symbol": symbol,
        "bias": "LONG",   # пока LONG only
        "impulse_high": last.high,
        "impulse_low": last.low,
        "atr": atr
    }