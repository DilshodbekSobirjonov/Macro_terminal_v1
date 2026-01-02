from services.exchange import ExchangeService
from core.candles import CandleFrame
from core.scoring import calculate_score

exchange = ExchangeService()

symbol = "BTCUSDT"
tf = "30m"

ohlcv = exchange.fetch_ohlcv(symbol, tf, limit=200)
oi_series = exchange.fetch_open_interest_history(symbol, tf, limit=200)

candles = CandleFrame(ohlcv, oi_series)

score, reasons = calculate_score(candles.candles)

print("SCORE:", score)
print("REASONS:")
for r in reasons:
    print("-", r)
