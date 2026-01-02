from services.exchange import ExchangeService
from core.candles import CandleFrame
from core.regime import market_regime

exchange = ExchangeService()

ohlcv = exchange.fetch_ohlcv("BTCUSDT", "4h", limit=250)
candles = CandleFrame(ohlcv)

print("MARKET REGIME:", market_regime(candles.candles))