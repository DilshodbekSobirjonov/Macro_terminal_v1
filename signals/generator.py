# signals/generator.py

from services.exchange import ExchangeService
from services.indicators import EMA, ATR
from services.structure import detect_strong_bos
from core.candles import CandleFrame

exchange = ExchangeService()

TIMEFRAME = "30m"


def get_htf_bias(symbol):
    ohlcv = exchange.fetch_ohlcv(symbol, "4h", limit=200)
    if not ohlcv:
        return None

    candles = CandleFrame(ohlcv).candles
    ema50 = EMA(candles, 50)
    ema200 = EMA(candles, 200)

    if ema50[-1] > ema200[-1]:
        return "LONG"
    if ema50[-1] < ema200[-1]:
        return "SHORT"
    return None


def generate_signal(symbol):
    """
    IMPULSE DETECTOR (НЕ ВХОД)
    """
    bias = get_htf_bias(symbol)
    if bias is None:
        return None

    ohlcv = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=200)
    oi = exchange.fetch_open_interest_history(symbol, TIMEFRAME, limit=200)

    if not ohlcv:
        return None

    candles = CandleFrame(ohlcv, oi).candles

    # 1️⃣ Strong BOS в сторону HTF
    if not detect_strong_bos(candles, bias):
        return None

    # 2️⃣ ATR filter (не перегрето)
    atr = ATR(candles, 14)
    atr_now = atr[-1]
    atr_mean = sum(atr[-20:]) / 20

    if atr_now > atr_mean * 1.6:
        return None

    # 3️⃣ Volume spike
    volumes = [c.volume for c in candles[-20:]]
    vol_mean = sum(volumes) / len(volumes)
    if candles[-1].volume < vol_mean * 1.7:
        return None

    # 4️⃣ OI direction
    if not oi or len(oi) < 2:
        return None

    oi_delta = oi[-1]["openInterest"] - oi[-2]["openInterest"]

    if bias == "LONG" and oi_delta <= 0:
        return None
    if bias == "SHORT" and oi_delta >= 0:
        return None

    # ⛔ НЕ ВХОДИМ, ТОЛЬКО ФИКСИРУЕМ ИМПУЛЬС
    return {
        "symbol": symbol,
        "bias": bias,
        "impulse_high": candles[-1].high,
        "impulse_low": candles[-1].low,
        "atr": atr_now
    }