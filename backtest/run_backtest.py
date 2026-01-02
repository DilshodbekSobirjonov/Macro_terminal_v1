# backtest/run_backtest.py

from services.exchange import ExchangeService
from core.candles import CandleFrame
from core.structure import MarketStructure
from core.indicators import calculate_atr, atr_regime, volume_anomaly
from trades.exits import calc_sl_tp

# ================= CONFIG =================

TIMEFRAME = "30m"
SYMBOLS = ["SOLUSDT", "INJUSDT", "OPUSDT", "AVAXUSDT", "MATICUSDT"]

LOOKBACK = 200
FUTURE_BARS = 20
COOLDOWN = 10

# ================= INIT =================

exchange = ExchangeService()

print("\nRunning SIMPLE backtest (NO OI, NO LIVE LOOPS)")
print(f"Timeframe: {TIMEFRAME}")
print("Symbols:", ", ".join(SYMBOLS))
print("-----\n")

total_results = []

# ================= BACKTEST =================

for symbol in SYMBOLS:
    print(f"{symbol}: fetching data...")
    ohlcv = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=LOOKBACK)

    if not ohlcv:
        print(f"{symbol}: no data")
        continue

    candles = CandleFrame(ohlcv).candles
    trades = []
    i = 50

    while i < len(candles) - FUTURE_BARS:
        window = candles[:i]
        structure = MarketStructure(window)

        # 1️⃣ BOS
        if not structure.detect_bos():
            i += 1
            continue

        # 2️⃣ ATR regime
        if atr_regime(window) != "expansion":
            i += 1
            continue

        # 3️⃣ Volume spike
        if not volume_anomaly(window, multiplier=1.5):
            i += 1
            continue

        atr = calculate_atr(window)
        if atr is None:
            i += 1
            continue

        entry = window[-1].close
        impulse = {
            "impulse_low": window[-1].low,
            "atr": atr
        }

        sl, tp = calc_sl_tp(entry, impulse)

        # ==== SIMULATION ====
        result = None
        for c in candles[i + 1:i + FUTURE_BARS]:
            if c.low <= sl:
                result = (sl - entry) / entry * 100
                break
            if c.high >= tp:
                result = (tp - entry) / entry * 100
                break

        if result is None:
            last = candles[i + FUTURE_BARS].close
            result = (last - entry) / entry * 100

        trades.append(result)
        total_results.append(result)

        i += COOLDOWN

    # ===== STATS =====
    if trades:
        wins = [t for t in trades if t > 0]
        winrate = len(wins) / len(trades) * 100
        avg = sum(trades) / len(trades)

        print(
            f"{symbol}: trades={len(trades)} | "
            f"winrate={winrate:.2f}% | avg={avg:.2f}%"
        )
    else:
        print(f"{symbol}: no trades")

# ================= TOTAL =================

print("\n=====")
print("===== TOTAL RESULT\n")

if total_results:
    wins = [t for t in total_results if t > 0]
    winrate = len(wins) / len(total_results) * 100
    avg = sum(total_results) / len(total_results)

    print(f"Total trades: {len(total_results)}")
    print(f"Total winrate: {winrate:.2f}%")
    print(f"Total avg: {avg:.2f}%")
    print(f"Best: {max(total_results):.2f}%")
    print(f"Worst: {min(total_results):.2f}%")
else:
    print("No trades executed")