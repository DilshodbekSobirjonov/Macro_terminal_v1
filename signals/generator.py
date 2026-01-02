# signals/generator.py

from services.exchange import ExchangeService
from core.candles import CandleFrame
from core.structure import detect_strong_bos
from core.indicators import calculate_atr, volume_anomaly, oi_delta_positive, atr_regime

exchange = ExchangeService()

TIMEFRAME = "30m"


def generate_signal(symbol):
    """
    IMPULSE DETECTOR
    Возвращает impulse или None
    """
    ohlcv = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=200)
    oi = exchange.fetch_open_interest_history(symbol, TIMEFRAME, limit=200)

    if not ohlcv:
        return None

    candles = CandleFrame(ohlcv, oi).candles

    # 1️⃣ Strong BOS
    if not detect_strong_bos(candles):
        return None

    # 2️⃣ ATR regime — не перегрето
    atr_state = atr_regime(candles)
    if atr_state != "expansion":
        return None

    # 3️⃣ Volume anomaly
    if not volume_anomaly(candles, multiplier=1.5):
        return None

    # 4️⃣ OI direction
    if not oi_delta_positive(candles):
        return None

    # 5️⃣ ATR value (для SL)
    atr = calculate_atr(candles)
    if atr is None:
        return None

    return {
        "symbol": symbol,
        "bias": "LONG",  # пока только long, как у тебя в логике
        "impulse_high": candles[-1].high,
        "impulse_low": candles[-1].low,
        "atr": atr
    }