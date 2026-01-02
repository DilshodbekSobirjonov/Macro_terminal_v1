# main.py

import time
from services.exchange import ExchangeService
from services.telegram import TelegramService

from core.candles import CandleFrame
from core.scoring import calculate_score
from core.structure import MarketStructure

from trades.trade import Trade
from trades.monitor import monitor_trade

# ================= CONFIG =================

SYMBOLS = [
    "BTCUSDT",
    # позже добавим альты
]

TIMEFRAME = "30m"

TELEGRAM_TOKEN = "PASTE_YOUR_BOT_TOKEN"
TELEGRAM_CHAT = "@YOUR_CHANNEL_OR_ID"

MIN_SCORE = 5

# ==========================================

exchange = ExchangeService()
telegram = TelegramService(TELEGRAM_TOKEN, TELEGRAM_CHAT)

active_trades = []


def run_cycle():
    global active_trades

    for symbol in SYMBOLS:
        # 1️⃣ DATA
        ohlcv = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=200)
        oi_series = exchange.fetch_open_interest_history(symbol, TIMEFRAME, limit=200)

        candles = CandleFrame(ohlcv, oi_series)

        # 2️⃣ SCORING
        score, reasons = calculate_score(candles.candles)

        structure = MarketStructure(candles.candles)

        # 3️⃣ ENTRY LOGIC
        if score >= MIN_SCORE and structure.detect_choch():
            entry_price = candles.candles[-1].close

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

            telegram.send(
                f"🟢 SIGNAL\n\n"
                f"{symbol}\n"
                f"ENTRY: {entry_price}\n"
                f"SCORE: {score}\n\n"
                + "\n".join(f"• {r}" for r in reasons)
            )

        # 4️⃣ MONITORING
        for trade in active_trades[:]:
            event = monitor_trade(trade, candles.candles)

            if event:
                if trade.state == "CLOSED":
                    telegram.send(
                        f"❌ CLOSED\n\n"
                        f"{trade.pair}\n"
                        f"Result: {trade.current_profit:.2f}%\n"
                        f"Reason: {trade.closed_reason}"
                    )
                    active_trades.remove(trade)
                else:
                    telegram.send(
                        f"📈 UPDATE\n\n"
                        f"{trade.pair}\n"
                        f"PNL: {trade.current_profit:.2f}%"
                    )


if __name__ == "__main__":
    telegram.send("🤖 MacroTerminal started")

    while True:
        try:
            run_cycle()
            time.sleep(30 * 60)  # 30 минут
        except Exception as e:
            telegram.send(f"⚠️ ERROR:\n{str(e)}")
            time.sleep(60)
