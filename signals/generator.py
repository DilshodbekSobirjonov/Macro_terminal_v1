# signals/generator.py

from services.market import get_candles, get_oi_delta
from services.indicators import EMA, ATR
from services.structure import detect_strong_bos

def get_htf_bias(symbol):
    htf = get_candles(symbol, "4h", 200)
    ema50 = EMA(htf, 50)
    ema200 = EMA(htf, 200)

    if ema50[-1] > ema200[-1]:
        return "LONG"
    if ema50[-1] < ema200[-1]:
        return "SHORT"
    return None


def generate_signal(symbol):
    bias = get_htf_bias(symbol)
    if bias is None:
        return None

    candles = get_candles(symbol, "30m", 200)

    if not detect_strong_bos(candles, bias):
        return None

    atr = ATR(candles, 14)[-1]
    atr_mean = sum(ATR(candles, 14)[-20:]) / 20
    if atr > atr_mean * 1.6:
        return None  # перегрето

    vol = candles[-1].volume
    mean_vol = sum(c.volume for c in candles[-20:]) / 20
    if vol < mean_vol * 1.7:
        return None

    oi = get_oi_delta(symbol)
    if bias == "LONG" and oi <= 0:
        return None
    if bias == "SHORT" and oi >= 0:
        return None

    # ⛔ НЕ ВХОД
    return {
        "symbol": symbol,
        "bias": bias,
        "impulse_high": candles[-1].high,
        "impulse_low": candles[-1].low,
        "atr": atr,
        "time": candles[-1].time
    }
