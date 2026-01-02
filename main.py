# main.py

import time
import os
import threading
from datetime import datetime, timezone
from dotenv import load_dotenv

from services.exchange import ExchangeService
from services.telegram import TelegramService
from services.db import Database
from services.commands import handle_command

from core.candles import CandleFrame
from core.scoring import calculate_score
from core.structure import MarketStructure
from core.regime import market_regime

from trades.trade import Trade
from trades.monitor import monitor_trade
from config.symbols import SYMBOLS

# ================= LOAD ENV =================

load_dotenv()

TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHANNEL_ID = os.getenv("TG_CHANNEL_ID")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

if not TG_TOKEN or not TG_CHANNEL_ID or not ADMIN_CHAT_ID:
    raise RuntimeError("Telegram ENV variables not set")

# ================= CONFIG =================

TIMEFRAME = "30m"
MIN_SCORE = 5

# ==========================================

exchange = ExchangeService()
telegram = TelegramService(TG_TOKEN, TG_CHANNEL_ID, ADMIN_CHAT_ID)
db = Database()

active_trades = db.load_active_trades()

# Глобальное состояние для команд
current_regime = "UNKNOWN"
last_cycle_time = "N/A"

# ==========================================


def run_cycle():
    global active_trades, current_regime, last_cycle_time

    last_cycle_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    analyzed = []
    signals = 0

    # 🌍 MARKET REGIME (BTC 4H)
    btc_ohlcv = exchange.fetch_ohlcv("BTCUSDT", "4h", limit=250)
    btc_candles = CandleFrame(btc_ohlcv)
    current_regime = market_regime(btc_candles.candles)

    for symbol in SYMBOLS:
        # 1️⃣ DATA
        ohlcv = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=200)
        oi_series = exchange.fetch_open_interest_history(symbol, TIMEFRAME, limit=200)
        candles = CandleFrame(ohlcv, oi_series)

        analyzed.append(symbol)

        # 2️⃣ SCORING
        score, reasons = calculate_score(candles.candles)
        structure = MarketStructure(candles.candles)

        # 3️⃣ ENTRY LOGIC
        if (
            current_regime == "RISK_ON"
            and score >= MIN_SCORE
            and structure.detect_choch()
            and not any(t.pair == symbol and t.state == "ACTIVE" for t in active_trades)
        ):
            entry_price = candles.candles[-2].close

            trade = Trade(
                pair=symbol,
                direction="LONG",
                entry_price=entry_price,
                score=score,
                reasons=reasons,
                tp_levels=[3, 6, 10],
                sl_percent=4.5
            )

            active_trades.append(trade)
            db.save_trade(trade)
            signals += 1

            telegram.send_channel(
                f"🟢 <b>SIGNAL</b>\n\n"
                f"<b>PAIR:</b> {symbol}\n"
                f"<b>ENTRY:</b> {entry_price}\n"
                f"<b>SCORE:</b> {score}\n\n"
                + "\n".join(f"• {r}" for r in reasons)
            )

        # 4️⃣ MONITORING
        for trade in active_trades[:]:
            event = monitor_trade(trade, candles.candles)

            if event and trade.state == "CLOSED":
                db.close_trade(trade)

                telegram.send_channel(
                    f"❌ <b>CLOSED</b>\n\n"
                    f"{trade.pair}\n"
                    f"Result: {trade.current_profit:.2f}%\n"
                    f"Reason: {trade.closed_reason}"
                )

                active_trades.remove(trade)

    # 👤 HEARTBEAT В ЛИЧКУ
    telegram.send_admin(
        f"🧠 <b>MacroTerminal heartbeat</b>\n\n"
        f"Time: {last_cycle_time}\n"
        f"Market regime: {current_regime}\n"
        f"Analyzed symbols: {len(analyzed)}\n"
        f"Signals this cycle: {signals}\n"
        f"Active trades: {len(active_trades)}"
    )


# ================= LOOPS ===================

def market_loop():
    while True:
        try:
            run_cycle()
            time.sleep(30 * 60)  # 30 минут
        except Exception as e:
            telegram.send_admin(f"⚠️ MARKET ERROR:\n{str(e)}")
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

            time.sleep(3)  # быстрый отклик
        except Exception as e:
            telegram.send_admin(f"⚠️ COMMAND ERROR:\n{str(e)}")
            time.sleep(5)


# ================= START ===================

if __name__ == "__main__":
    telegram.send_admin("🤖 MacroTerminal started")

    t1 = threading.Thread(target=market_loop, daemon=True)
    t2 = threading.Thread(target=command_loop, daemon=True)

    t1.start()
    t2.start()

    t1.join()
    t2.join()