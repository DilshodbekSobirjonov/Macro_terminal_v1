from services.exchange import ExchangeService
from core.candles import CandleFrame

exchange = ExchangeService()

symbol = "BTC/USDT"
tf = "30m"

ohlcv = exchange.fetch_ohlcv(symbol, tf, limit=100)

# Пока без OI
candles = CandleFrame(ohlcv)

last = candles.last_closed()
print(last)
