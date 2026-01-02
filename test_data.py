from services.exchange import ExchangeService
from core.candles import CandleFrame
from core.scoring import calculate_score
from trades.trade import Trade
from trades.monitor import monitor_trade

exchange = ExchangeService()

symbol = "BTCUSDT"
tf = "30m"

ohlcv = exchange.fetch_ohlcv(symbol, tf, limit=200)
oi_series = exchange.fetch_open_interest_history(symbol, tf, limit=200)

candles = CandleFrame(ohlcv, oi_series)

score, reasons = calculate_score(candles.candles)

print("SCORE:", score)
print("REASONS:", reasons)

# ❗ ИСКУССТВЕННАЯ СДЕЛКА ДЛЯ ТЕСТА
trade = Trade(
    pair=symbol,
    direction="LONG",
    entry_price=candles.candles[-1].close,
    score=score,
    reasons=reasons,
    tp_levels=[3, 6, 10],
    sl_percent=4.5
)

event = monitor_trade(trade, candles.candles)
print("TRADE EVENT:", event)
print("CURRENT PNL:", trade.current_profit)
print("STATE:", trade.state)
