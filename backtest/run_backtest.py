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

SYMBOL = "SOLUSDT"      # BTCUSDT | SOLUSDT | INJUSDT | OPUSDT
TIMEFRAME = "30m"
LIMIT = 1500

MIN_SCORE = 4
TP_PERCENT = 6.0
SL_PERCENT = 4.5

COOLDOWN_CANDLES = 20   # запрет повторного входа

# ========================================

exchange = ExchangeService()


def run():
    print("Running backtest...")
    print("Symbol:", SYMBOL)

    ohlcv = exchange.fetch_ohlcv(
        SYMBOL,
        TIMEFRAME,
        limit=LIMIT
    )

    oi = exchange.fetch_open_interest_history(
        SYMBOL,
        TIMEFRAME,
        limit=LIMIT
    )

    if not ohlcv:
        print("No OHLCV data")
        return

    candles = CandleFrame(
        ohlcv,
        oi
    ).candles

    trades = []
    active_trade = None
    last_exit_index = -1000

    for i in range(50, len(candles)):
        window = candles[:i]
        last = window[-1]

        score, reasons = calculate_score(window)

        # ---------- ENTRY ----------
        if (
            active_trade is None
            and score >= MIN_SCORE
            and i - last_exit_index > COOLDOWN_CANDLES
        ):
            entry_price = last.close

            sl_price = entry_price * (1 - SL_PERCENT / 100)
            tp_price = entry_price * (1 + TP_PERCENT / 100)

            active_trade = {
                "entry": entry_price,
                "sl": sl_price,
                "tp": tp_price,
                "open_index": i
            }

        # ---------- EXIT ----------
        if active_trade is not None:
            if last.low <= active_trade["sl"]:
                trades.append(-SL_PERCENT)
                last_exit_index = i
                active_trade = None

            elif last.high >= active_trade["tp"]:
                trades.append(TP_PERCENT)
                last_exit_index = i
                active_trade = None

    # ---------- RESULTS ----------
    print("\n===== BACKTEST RESULT =====")
    print("Symbol:", SYMBOL)
    print("Trades:", len(trades))

    if trades:
        wins = [t for t in trades if t > 0]
        losses = [t for t in trades if t < 0]

        print("Winrate:", round(len(wins) / len(trades) * 100, 2), "%")
        print("Avg:", round(sum(trades) / len(trades), 2), "%")
        print("Best:", max(trades), "%")
        print("Worst:", min(trades), "%")
    else:
        print("No trades")


if __name__ == "__main__":
    run()