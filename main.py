# main.py

import os
import time
import threading
from datetime import datetime, timezone

from dotenv import load_dotenv

from services.exchange import ExchangeService
from services.telegram import TelegramService
from services.db import Database
from services.commands import handle_command
from services.stats import calculate_stats, daily_range
from services.logger import setup_logger

from core.candles import CandleFrame
from core.scoring import calculate_score
from core.structure import MarketStructure
from core.regime import market_regime
from core.universe import filter_symbols

from trades.trade import Trade
from trades.monitor import monitor_trade

from signals.generator import generate_signal
from signals.validator import validate_entry
from trades.trade import open_trade, calc_sl_tp

impulse = generate_signal(symbol)

if impulse:
    entry_price = validate_entry(impulse)

    if entry_price:
        sl, tp = calc_sl_tp(entry_price, impulse)

        open_trade(
            symbol=symbol,
            side=impulse["bias"],
            entry_price=entry_price,
            stop_loss=sl,
            take_profit=tp
        )

# =========================================================
# ENV
# =========================================================

load_dotenv()

TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHANNEL_ID = os.getenv("TG_CHANNEL_ID")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

if not TG_TOKEN or not TG_CHANNEL_ID or not ADMIN_CHAT_ID:
    raise RuntimeError("Telegram ENV not set")

# =========================================================
# CONFIG
# =========================================================

TIMEFRAME = "30m"
MIN_SCORE = 5

MARKET_SLEEP = 30 * 60     # 30 min
COMMAND_SLEEP = 3          # 3 sec
WATCHDOG_TIMEOUT = 60 * 60 # 1 hour

# =========================================================
# SERVICES
# =========================================================

exchange = ExchangeService()
telegram = TelegramService(TG_TOKEN, TG_CHANNEL_ID, ADMIN_CHAT_ID)
db = Database()
logger = setup_logger()

active_trades = db.load_active_trades()

# shared state
current_regime = "UNKNOWN"
last_cycle_time = "N/A"
last_market_tick = time.time()

# =========================================================
# MARKET CYCLE
# =========================================================

def run_market_cycle():
    global active_trades, current_regime, last_cycle_time, last_market_tick

    last_market_tick = time.time()
    last_cycle_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    analyzed = 0
    signals = 0

    # -------- BTC REGIME --------
    btc_ohlcv = exchange.fetch_ohlcv("BTCUSDT", "4h", limit=250)
    btc_candles = CandleFrame(btc_ohlcv)
    current_regime = market_regime(btc_candles.candles)

    # -------- DYNAMIC UNIVERSE --------
    tickers = exchange.fetch_tickers()
    symbols = filter_symbols(tickers)

    for symbol in symbols:
        analyzed += 1

        # --- data ---
        ohlcv = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=200)
        oi = exchange.fetch_open_interest_history(symbol, TIMEFRAME, limit=200)

        if not ohlcv:
            continue

        candles = CandleFrame(ohlcv, oi)

        # --- scoring ---
        score, reasons = calculate_score(candles.candles)
        structure = MarketStructure(candles.candles)

        # --- entry ---
        if (
            current_regime == "RISK_ON"
            and score >= MIN_SCORE
            and structure.detect_choch()
            and not any(t.pair == symbol and t.state == "ACTIVE" for t in active_trades)
        ):
            entry = candles.candles[-2].close

            trade = Trade(
                pair=symbol,
                direction="LONG",
                entry_price=entry,
                score=score,
                reasons=reasons,
                tp_levels=[3, 6, 10],
                sl_percent=4.5
            )

            active_trades.append(trade)
            db.save_trade(trade)
            signals += 1

            logger.info(f"SIGNAL {symbol} score={score}")

            telegram.send_channel(
                f"🟢 <b>SIGNAL</b>\n\n"
                f"{symbol}\n"
                f"ENTRY: {entry}\n"
                f"SCORE: {score}\n\n"
                + "\n".join(f"• {r}" for r in reasons)
            )

        # --- monitoring ---
        for trade in active_trades[:]:
            event = monitor_trade(trade, candles.candles)

            if event and trade.state == "CLOSED":
                db.close_trade(trade)
                active_trades.remove(trade)

                logger.info(
                    f"CLOSED {trade.pair} pnl={trade.current_profit:.2f}"
                )

                telegram.send_channel(
                    f"❌ <b>CLOSED</b>\n\n"
                    f"{trade.pair}\n"
                    f"Result: {trade.current_profit:.2f}%\n"
                    f"Reason: {trade.closed_reason}"
                )

    # -------- HEARTBEAT --------
    telegram.send_admin(
        f"🧠 <b>MacroTerminal heartbeat</b>\n\n"
        f"Time: {last_cycle_time}\n"
        f"Regime: {current_regime}\n"
        f"Universe: {len(symbols)}\n"
        f"Analyzed: {analyzed}\n"
        f"Signals: {signals}\n"
        f"Active trades: {len(active_trades)}"
    )

# =========================================================
# LOOPS
# =========================================================

def market_loop():
    while True:
        try:
            run_market_cycle()

            # daily stats @ 00 UTC
            if last_cycle_time.endswith("00 UTC"):
                results = db.get_closed_trades(daily_range())
                stats = calculate_stats(results)

                if stats:
                    telegram.send_admin(
                        f"📊 <b>DAILY STATS</b>\n\n"
                        f"Trades: {stats['trades']}\n"
                        f"Winrate: {stats['winrate']:.1f}%\n"
                        f"Avg: {stats['avg_return']:.2f}%\n"
                        f"Best: {stats['best']:.2f}%\n"
                        f"Worst: {stats['worst']:.2f}%"
                    )

            time.sleep(MARKET_SLEEP)

        except Exception as e:
            logger.error(str(e))
            time.sleep(60)


def command_loop():
    while True:
        try:
            state = {
                "regime": current_regime,
                "active_trades": active_trades,
                "last_heartbeat": last_cycle_time
            }

            commands = telegram.fetch_commands()
            for cmd in commands:
                reply = handle_command(cmd, state)
                if reply:
                    telegram.send_admin(reply)

            time.sleep(COMMAND_SLEEP)

        except Exception:
            time.sleep(5)


def watchdog_loop():
    while True:
        if time.time() - last_market_tick > WATCHDOG_TIMEOUT:
            telegram.send_admin("🛑 WATCHDOG: market loop stalled. Restart bot.")
            os._exit(1)
        time.sleep(60)

# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    telegram.send_admin("🤖 MacroTerminal started")
    logger.info("MacroTerminal boot")

    threading.Thread(target=market_loop, daemon=True).start()
    threading.Thread(target=command_loop, daemon=True).start()
    threading.Thread(target=watchdog_loop, daemon=True).start()

    while True:
        time.sleep(60)