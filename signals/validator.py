# signals/validator.py

from services.exchange import ExchangeService
from services.indicators import EMA
from services.structure import detect_choch
from core.candles import CandleFrame

exchange = ExchangeService()

LOW_TF = "5m"


def in_pullback(price, low, high):
    fib38 = low + 0.382 * (high - low)
    fib50 = low + 0.5 * (high - low)
    return fib38 <= price <= fib50


def validate_entry(impulse):
    """
    FINAL ENTRY CONFIRMATION
    """
    symbol = impulse["symbol"]
    bias = impulse["bias"]

    ohlcv = exchange.fetch_ohlcv(symbol, LOW_TF, limit=60)
    if not ohlcv:
        return None

    candles = CandleFrame(ohlcv).candles
    ema20 = EMA(candles, 20)

    last = candles[-1]

    # 1️⃣ Pullback
    if not in_pullback(
        last.close,
        impulse["impulse_low"],
        impulse["impulse_high"]
    ):
        return None

    # 2️⃣ CHoCH
    if not detect_choch(candles, bias):
        return None

    # 3️⃣ Rejection candle
    body = abs(last.close - last.open)
    rng = last.high - last.low

    if rng == 0 or body / rng < 0.4:
        return None

    # 4️⃣ EMA alignment
    if bias == "LONG" and last.close < ema20[-1]:
        return None
    if bias == "SHORT" and last.close > ema20[-1]:
        return None

    return last.close
