from services.exchange import ExchangeService
from core.candles import CandleFrame
from core.structure import MarketStructure
from core.indicators import calculate_atr, atr_regime

exchange = ExchangeService()

symbol = "BTCUSDT"
tf = "30m"

ohlcv = exchange.fetch_ohlcv(symbol, tf, limit=150)
candles = CandleFrame(ohlcv)

structure = MarketStructure(candles.candles)

atr = calculate_atr(candles.candles)
regime = atr_regime(candles.candles)

print("ATR:", atr)
print("ATR regime:", regime)
print("BOS:", structure.detect_bos())
print("CHoCH:", structure.detect_choch())
