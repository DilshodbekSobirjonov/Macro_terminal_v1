# signals/validator.py

from services.market import get_candles, get_cvd
from services.indicators import EMA
from services.structure import detect_choch

def in_pullback(price, impulse):
    low = impulse["impulse_low"]
    high = impulse["impulse_high"]
    fib38 = low + 0.382 * (high - low)
    fib50 = low + 0.5 * (high - low)
    return fib38 <= price <= fib50


def validate_entry(impulse):
    symbol = impulse["symbol"]
    bias = impulse["bias"]

    candles = get_candles(symbol, "5m", 50)
    ema20 = EMA(candles, 20)

    last = candles[-1]

    # 1️⃣ pullback
    if not in_pullback(last.close, impulse):
        return None

    # 2️⃣ CHoCH
    if not detect_choch(candles, bias):
        return None

    # 3️⃣ rejection candle
    body = abs(last.close - last.open)
    rng = last.high - last.low
    if rng == 0 or body / rng < 0.4:
        return None

    # 4️⃣ EMA alignment
    if bias == "LONG" and last.close < ema20[-1]:
        return None
    if bias == "SHORT" and last.close > ema20[-1]:
        return None

    # 5️⃣ CVD
    cvd = get_cvd(symbol)
    if bias == "LONG" and cvd < 0:
        return None
    if bias == "SHORT" and cvd > 0:
        return None

    return last.close
