from services.exchange import ExchangeService
from core.candles import CandleFrame

exchange = ExchangeService()

symbol = "BTCUSDT"   # ВАЖНО: без /
tf = "30m"

ohlcv = exchange.fetch_ohlcv(symbol, tf, limit=100)

candles = CandleFrame(ohlcv)

last = candles.last_closed()
print(last)
