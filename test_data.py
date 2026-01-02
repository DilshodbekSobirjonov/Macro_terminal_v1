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

symbol = "BTCUSDT"
tf = "30m"

ohlcv = exchange.fetch_ohlcv(symbol, tf, limit=150)
oi_series = exchange.fetch_open_interest_history(symbol, tf, limit=150)

candles = CandleFrame(ohlcv, oi_series)

structure = MarketStructure(candles.candles)

print("ATR regime:", atr_regime(candles.candles))
print("Volume anomaly:", volume_anomaly(candles.candles))
print("OI positive:", oi_delta_positive(candles.candles))
print("BOS:", structure.detect_bos())
print("CHoCH:", structure.detect_choch())
