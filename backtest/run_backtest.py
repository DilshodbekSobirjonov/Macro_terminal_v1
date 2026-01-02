# backtest/run_backtest.py

import sys
import os

# добавляем корень проекта
sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

from services.exchange import ExchangeService
from core.candles import CandleFrame
from core.scoring import calculate_score

# ================= CONFIG =================

SYMBOLS = [
    "SOLUSDT",
    "INJUSDT",
    "OPUSDT",
    "AVAXUSDT",
    "MATICUSDT"
]

TIMEFRAME = "30m"
LIMIT = 1500

MIN_SCORE = 4
TP_PERCENT = 6.0
SL_PERCENT = 4.5
COOLDOWN_CANDLES = 20

# ========================================

exchange = ExchangeService()


def run_symbol(symbol):
    ohlcv = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=LIMIT)
    oi = exchange.fetch_open_interest_history(symbol, TIMEFRAME, limit=LIMIT)

    if not ohlcv:
        return []

    candles = CandleFrame(ohlcv, oi).candles

    trades = []
    active_trade = None
    last_exit_index = -1000
    pending_signal = None

    for i in range(50, len(candles)):
        window = candles[:i]
        last = window[-1]

        score, _ = calculate_score(window)

        # SIGNAL
        if (
            pending_signal is None
            and active_trade is None
            and score >= MIN_SCORE
            and i - last_exit_index > COOLDOWN_CANDLES
        ):
            pending_signal = {
                "high": last.high,
                "index": i
            }

        # CONFIRMATION ENTRY
        if pending_signal is not None and active_trade is None:
            if last.close > pending_signal["high"]:
                entry = last.close
                sl = entry * (1 - SL_PERCENT / 100)
                tp = entry * (1 + TP_PERCENT / 100)

                active_trade = {
                    "sl": sl,
                    "tp": tp
                }
                pending_signal = None

            elif i - pending_signal["index"] > 5:
                pending_signal = None

        # EXIT
        if active_trade is not None:
            if last.low <= active_trade["sl"]:
                trades.append(-SL_PERCENT)
                last_exit_index = i
                active_trade = None

            elif last.high >= active_trade["tp"]:
                trades.append(TP_PERCENT)
                last_exit_index = i
                active_trade = None

    return trades


def run():
    print("Running MULTI backtest")
    print("Timeframe:", TIMEFRAME)
    print("Symbols:", ", ".join(SYMBOLS))
    print("-" * 40)

    all_trades = []

    for symbol in SYMBOLS:
        trades = run_symbol(symbol)
        all_trades.extend(trades)

        if trades:
            wins = [t for t in trades if t > 0]
            avg = sum(trades) / len(trades)

            print(
                f"{symbol}: trades={len(trades)} | "
                f"winrate={round(len(wins)/len(trades)*100,2)}% | "
                f"avg={round(avg,2)}%"
            )
        else:
            print(f"{symbol}: no trades")

    print("\n===== TOTAL RESULT =====")
    print("Total trades:", len(all_trades))

    if all_trades:
        wins = [t for t in all_trades if t > 0]

        print("Total winrate:", round(len(wins)/len(all_trades)*100, 2), "%")
        print("Total avg:", round(sum(all_trades)/len(all_trades), 2), "%")
        print("Best:", max(all_trades), "%")
        print("Worst:", min(all_trades), "%")
    else:
        print("No trades at all")


if __name__ == "__main__":
    run()