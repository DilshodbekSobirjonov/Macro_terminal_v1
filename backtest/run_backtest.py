# backtest/run_backtest.py

import time
from datetime import datetime

from services.exchange import ExchangeService
from core.candles import CandleFrame

from signals.generator import generate_signal
from signals.validator import validate_entry
from trades.trade import calc_sl_tp

# =========================================================
# CONFIG
# =========================================================

TIMEFRAME = "30m"
START_BALANCE = 10000.0

SYMBOLS = [
    "SOLUSDT",
    "INJUSDT",
    "OPUSDT",
    "AVAXUSDT",
    "MATICUSDT"
]

COMMISSION = 0.0004   # 0.04%
SLIPPAGE = 0.0005     # 0.05%

# =========================================================
# SERVICES
# =========================================================

exchange = ExchangeService()

# =========================================================
# BACKTEST CORE
# =========================================================

class SimTrade:
    def __init__(self, symbol, side, entry, sl, tp):
        self.symbol = symbol
        self.side = side
        self.entry = entry
        self.sl = sl
        self.tp = tp
        self.closed = False
        self.result = 0.0


def simulate_trade(trade, candles):
    """
    Candle-by-candle simulation AFTER entry candle
    """
    for c in candles:
        if trade.side == "LONG":
            if c.low <= trade.sl:
                trade.result = (trade.sl - trade.entry) / trade.entry * 100
                trade.closed = True
                return
            if c.high >= trade.tp:
                trade.result = (trade.tp - trade.entry) / trade.entry * 100
                trade.closed = True
                return
        else:
            if c.high >= trade.sl:
                trade.result = (trade.entry - trade.sl) / trade.entry * 100
                trade.closed = True
                return
            if c.low <= trade.tp:
                trade.result = (trade.entry - trade.tp) / trade.entry * 100
                trade.closed = True
                return

    # time exit (no hit)
    last = candles[-1].close
    if trade.side == "LONG":
        trade.result = (last - trade.entry) / trade.entry * 100
    else:
        trade.result = (trade.entry - last) / trade.entry * 100

    trade.closed = True


# =========================================================
# RUN BACKTEST
# =========================================================

print("\nRunning MULTI backtest")
print(f"Timeframe: {TIMEFRAME}")
print("Symbols:", ", ".join(SYMBOLS))
print("-----\n")

total_trades = []
balance = START_BALANCE

for symbol in SYMBOLS:
    ohlcv = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=1500)
    oi = exchange.fetch_open_interest_history(symbol, TIMEFRAME, limit=1500)

    if not ohlcv:
        print(f"{symbol}: no data")
        continue

    candles = CandleFrame(ohlcv, oi).candles

    trades = []
    i = 50  # start after warmup

    while i < len(candles) - 20:
        # 🔹 IMPULSE DETECTION
        impulse = generate_signal(symbol)
        if not impulse:
            i += 1
            continue

        # 🔹 ENTRY CONFIRMATION
        entry_price = validate_entry(impulse)
        if not entry_price:
            i += 1
            continue

        # 🔹 SL / TP
        sl, tp = calc_sl_tp(entry_price, impulse)

        # slippage + commission
        entry_price *= (1 + SLIPPAGE if impulse["bias"] == "LONG" else 1 - SLIPPAGE)

        trade = SimTrade(
            symbol=symbol,
            side=impulse["bias"],
            entry=entry_price,
            sl=sl,
            tp=tp
        )

        simulate_trade(trade, candles[i + 1:i + 30])

        # commission
        trade.result -= COMMISSION * 100 * 2
        trades.append(trade)
        total_trades.append(trade)

        i += 10  # cooldown

    # ===== SYMBOL STATS =====
    if trades:
        wins = [t for t in trades if t.result > 0]
        winrate = len(wins) / len(trades) * 100
        avg = sum(t.result for t in trades) / len(trades)

        print(
            f"{symbol}: trades={len(trades)} | "
            f"winrate={winrate:.2f}% | avg={avg:.2f}%"
        )
    else:
        print(f"{symbol}: no trades")

print("\n=====")
print("===== TOTAL RESULT\n")

if total_trades:
    wins = [t for t in total_trades if t.result > 0]
    winrate = len(wins) / len(total_trades) * 100
    avg = sum(t.result for t in total_trades) / len(total_trades)
    best = max(t.result for t in total_trades)
    worst = min(t.result for t in total_trades)

    print(f"Total trades: {len(total_trades)}")
    print(f"Total winrate: {winrate:.2f} %")
    print(f"Total avg: {avg:.2f} %")
    print(f"Best: {best:.2f}%")
    print(f"Worst: {worst:.2f}%")
else:
    print("No trades executed")