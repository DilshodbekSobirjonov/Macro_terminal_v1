# backtest/run_backtest.py
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime
from services.exchange import ExchangeService
from core.candles import CandleFrame
from core.scoring import calculate_score
from core.structure import MarketStructure
from core.regime import market_regime
from trades.trade import Trade
from trades.monitor import monitor_trade

SYMBOL = "BTCUSDT"
TIMEFRAME = "30m"
LIMIT = 3000          # ~60 дней для 30m
MIN_SCORE = 5

exchange = ExchangeService()

def run():
    ohlcv = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=LIMIT)
    oi = exchange.fetch_open_interest_history(SYMBOL, TIMEFRAME, limit=LIMIT)
    candles = CandleFrame(ohlcv, oi).candles

    trades = []
    active_trade = None

    # regime считаем на старшем ТФ
    btc_ohlcv_4h = exchange.fetch_ohlcv("BTCUSDT", "4h", limit=500)
    btc_candles_4h = CandleFrame(btc_ohlcv_4h).candles
    regime = market_regime(btc_candles_4h)

    for i in range(100, len(candles)):
        window = candles[:i]
        last = window[-1]

        score, reasons = calculate_score(window)
        structure = MarketStructure(window)

        # ENTRY
        if (
            not active_trade
            and regime == "RISK_ON"
            and score >= MIN_SCORE
            and structure.detect_choch()
        ):
            active_trade = Trade(
                pair=SYMBOL,
                direction="LONG",
                entry_price=last.close,
                score=score,
                reasons=reasons,
                tp_levels=[3, 6, 10],
                sl_percent=4.5
            )

        # MONITOR
        if active_trade:
            event = monitor_trade(active_trade, window)
            if event and active_trade.state == "CLOSED":
                trades.append(active_trade)
                active_trade = None

    # -------- STATS --------
    results = [t.current_profit for t in trades]
    wins = [r for r in results if r > 0]
    losses = [r for r in results if r <= 0]

    print("\n===== BACKTEST RESULT =====")
    print("Symbol:", SYMBOL)
    print("Trades:", len(results))
    if results:
        print("Winrate:", round(len(wins) / len(results) * 100, 2), "%")
        print("Avg:", round(sum(results) / len(results), 2), "%")
        print("Best:", round(max(results), 2), "%")
        print("Worst:", round(min(results), 2), "%")
    else:
        print("No trades")

if __name__ == "__main__":
    run()