# backtest/run_backtest.py

from services.exchange import ExchangeService

from core.candles import CandleFrame
from core.structure import MarketStructure
from core.indicators import (
    calculate_atr,
    atr_regime,
    volume_anomaly
)
from core.regime import market_regime

from trades.exits import calc_sl_tp

# =========================================================
# CONFIG
# =========================================================

TIMEFRAME = "30m"
HTF_TIMEFRAME = "4h"

SYMBOLS = [
    "SOLUSDT",
    "INJUSDT",
    "OPUSDT",
    "AVAXUSDT",
    "MATICUSDT"
]

LOOKBACK = 300        # сколько свечей грузим
START_INDEX = 60      # прогрев
FUTURE_BARS = 20      # сколько баров смотрим вперёд
COOLDOWN = 10         # пауза между сделками

# =========================================================
# INIT
# =========================================================

exchange = ExchangeService()

print("\nRunning BACKTEST with BTC + HTF filter")
print(f"Timeframe: {TIMEFRAME}")
print("Symbols:", ", ".join(SYMBOLS))
print("------------------------------------------------\n")

# =========================================================
# BTC CONTEXT (ONCE)
# =========================================================

print("Fetching BTC context...")
btc_ohlcv = exchange.fetch_ohlcv("BTCUSDT", HTF_TIMEFRAME, limit=300)

if not btc_ohlcv:
    raise RuntimeError("BTC data not available")

btc_candles = CandleFrame(btc_ohlcv).candles
btc_regime = market_regime(btc_candles)

print(f"BTC REGIME: {btc_regime}\n")

# =========================================================
# BACKTEST
# =========================================================

total_results = []

for symbol in SYMBOLS:
    print(f"{symbol}: fetching data...")

    ohlcv = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=LOOKBACK)
    if not ohlcv:
        print(f"{symbol}: no data\n")
        continue

    candles = CandleFrame(ohlcv).candles
    trades = []

    i = START_INDEX

    while i < len(candles) - FUTURE_BARS:

        # ================= BTC FILTER =================
        if btc_regime != "RISK_ON":
            i += 1
            continue

        window = candles[:i]

        # ================= HTF FILTER =================
        htf_ohlcv = exchange.fetch_ohlcv(symbol, HTF_TIMEFRAME, limit=200)
        if not htf_ohlcv:
            i += 1
            continue

        htf_candles = CandleFrame(htf_ohlcv).candles
        htf_structure = MarketStructure(htf_candles)

        if not htf_structure.detect_bos():
            i += 1
            continue

        # ================= LTF STRUCTURE =================
        structure = MarketStructure(window)

        if not structure.detect_bos():
            i += 1
            continue

        # ================= ATR REGIME =================
        if atr_regime(window) != "expansion":
            i += 1
            continue

        # ================= VOLUME FILTER =================
        if not volume_anomaly(window, multiplier=1.5):
            i += 1
            continue

        # ================= ATR =================
        atr = calculate_atr(window)
        if atr is None:
            i += 1
            continue

        # ================= ENTRY =================
        entry = window[-1].close
        impulse = {
            "impulse_low": window[-1].low,
            "atr": atr
        }

        sl, tp = calc_sl_tp(entry, impulse)

        # ================= SIMULATION =================
        result = None

        for c in candles[i + 1:i + FUTURE_BARS]:
            if c.low <= sl:
                result = (sl - entry) / entry * 100
                break
            if c.high >= tp:
                result = (tp - entry) / entry * 100
                break

        if result is None:
            last_close = candles[i + FUTURE_BARS].close
            result = (last_close - entry) / entry * 100

        trades.append(result)
        total_results.append(result)

        i += COOLDOWN

    # ================= SYMBOL STATS =================
    if trades:
        wins = [r for r in trades if r > 0]
        winrate = len(wins) / len(trades) * 100
        avg = sum(trades) / len(trades)

        print(
            f"{symbol}: trades={len(trades)} | "
            f"winrate={winrate:.2f}% | avg={avg:.2f}%"
        )
    else:
        print(f"{symbol}: no trades")

    print()

# =========================================================
# TOTAL STATS
# =========================================================

print("================================================")
print("TOTAL RESULT\n")

if total_results:
    wins = [r for r in total_results if r > 0]
    winrate = len(wins) / len(total_results) * 100
    avg = sum(total_results) / len(total_results)

    print(f"Total trades: {len(total_results)}")
    print(f"Total winrate: {winrate:.2f}%")
    print(f"Total avg: {avg:.2f}%")
    print(f"Best: {max(total_results):.2f}%")
    print(f"Worst: {min(total_results):.2f}%")
else:
    print("No trades executed")