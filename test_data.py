from services.exchange import ExchangeService
from core.candles import CandleFrame
from core.structure import MarketStructure

exchange = ExchangeService()

symbol = "BTCUSDT"
tf = "30m"

ohlcv = exchange.fetch_ohlcv(symbol, tf, limit=120)
candles = CandleFrame(ohlcv)

structure = MarketStructure(candles.candles)

print("Last swing high:", structure.last_swing_high())
print("Last swing low:", structure.last_swing_low())
print("BOS:", structure.detect_bos())
print("CHoCH:", structure.detect_choch())
