from services.exchange import ExchangeService
from core.candles import CandleFrame

exchange = ExchangeService()

symbol = "BTCUSDT"
tf = "30m"

ohlcv = exchange.fetch_ohlcv(symbol, tf, limit=100)

candles = CandleFrame(ohlcv)

last = candles.last_closed()

print("TIME:", last.time)
print("OPEN:", last.open)
print("HIGH:", last.high)
print("LOW:", last.low)
print("CLOSE:", last.close)
print("VOLUME:", last.volume)
