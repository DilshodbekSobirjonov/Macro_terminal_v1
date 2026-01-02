# backtest/run_backtest.py

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.exchange import ExchangeService
from core.candles import CandleFrame
from core.scoring import calculate_score
from core.indicators import calculate_atr
from trades.trade import Trade

SYMBOL = "BTCUSDT"
TIMEFRAME = "30m"
LIMIT = 3000
MIN_SCORE = 3

exchange = ExchangeService()

def run():
    ohlcv = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=LIMIT)
    oi = exchange.fetch_open_interest_history(SYMBOL, TIMEFRAME, limit=LIMIT)
    candles = CandleFrame(ohlcv, oi).candles

    trades = []
    active_trade = None

    for i in range(50, len(candles)):
        window = candles[:i]
        last = window[-1]

        score, reasons = calculate_score(window)
if score > 0:
        print(i, "SCORE:", score, reasons)
        atr = calculate_atr(window)

        # ENTRY (упрощённый, но честный)
        if not active_trade and score >= MIN_SCORE:
            entry = last.close
            sl = entry * (1 - 0.045)
            tp = entry * (1 + 0.06)

            active_trade = {
                "entry": entry,
                "sl": sl,
                "tp": tp,
                "open_index": i
            }

        # EXIT
        if active_trade:
            if last.low <= active_trade["sl"]:
                trades.append(-4.5)
                active_trade = None
            elif last.high >= active_trade["tp"]:
                trades.append(6.0)
                active_trade = None

    # STATS
    wins = [t for t in trades if t > 0]
    losses = [t for t in trades if t < 0]

    print("\n===== BACKTEST RESULT =====")
    print("Symbol:", SYMBOL)
    print("Trades:", len(trades))
    if trades:
        print("Winrate:", round(len(wins) / len(trades) * 100, 2), "%")
        print("Avg:", round(sum(trades) / len(trades), 2), "%")
        print("Best:", max(trades), "%")
        print("Worst:", min(trades), "%")
    else:
        print("No trades")

if __name__ == "__main__":
    run()