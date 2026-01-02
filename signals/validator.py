# signals/validator.py

from services.exchange import ExchangeService
from core.candles import CandleFrame
from core.structure import MarketStructure

exchange = ExchangeService()
LOW_TF = "5m"


def in_pullback(price, low, high):
    fib38 = low + 0.382 * (high - low)
    fib50 = low + 0.5 * (high - low)
    return fib38 <= price <= fib50


def validate_entry(impulse):
    symbol = impulse["symbol"]

    ohlcv = exchange.fetch_ohlcv(symbol, LOW_TF, limit=60)
    if not ohlcv:
        return None

    candles = CandleFrame(ohlcv)
    structure = MarketStructure(candles.candles)

    last = candles.candles[-1]

    # 1️⃣ Pullback
    if not in_pullback(
        last.close,
        impulse["impulse_low"],
        impulse["impulse_high"]
    ):
        return None

    # 2️⃣ CHoCH (реальный метод)
    if not structure.detect_choch():
        return None

    # 3️⃣ Rejection candle
    body = abs(last.close - last.open)
    rng = last.high - last.low

    if rng == 0 or body / rng < 0.4:
        return None

    return last.close
