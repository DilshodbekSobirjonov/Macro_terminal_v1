2# main.py

import os
import time
import threading
import sys
import subprocess
from datetime import datetime, timezone

from dotenv import load_dotenv

# ================= SERVICES =================
from config import *
from services.exchange import ExchangeService
from services.telegram import TelegramService
from services.db import Database
from services.commands import handle_command
from services.stats import calculate_stats, daily_range
from services.logger import setup_logger

# ================= CORE =================
from core.candles import CandleFrame
from core.regime import market_regime
from core.universe import filter_symbols

# ================= TRADES =================
from trades.trade import open_trade
from trades.exits import calc_sl_tp
from trades.monitor import monitor_trade

# ================= SIGNALS =================
from signals.generator import generate_signal
from signals.validator import validate_entry

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
BOT_START_TIME = time.time()
TIMEFRAME = "30m"

MARKET_SLEEP = 30 * 60      # 30 min
COMMAND_SLEEP = 3           # 3 sec
WATCHDOG_TIMEOUT = 60 * 60  # 1 hour

# =========================================================
# SERVICES INIT
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
    entries = 0

    # -------- BTC REGIME (GLOBAL CONTEXT) --------
    btc_ohlcv = exchange.fetch_ohlcv("BTCUSDT", "4h", limit=300)
    btc_candles = CandleFrame(btc_ohlcv)
    current_regime = market_regime(btc_candles.candles)

    # -------- DYNAMIC UNIVERSE --------
    tickers = exchange.fetch_tickers()
    symbols = filter_symbols(tickers)

    # -------- ENTRY LOGIC --------
    for symbol in symbols:
        analyzed += 1

        # skip if already in trade
        if any(t.pair == symbol and t.state == "ACTIVE" for t in active_trades):
            continue

        # regime filter
        if current_regime == "RISK_OFF":
            continue

        is_neutral = current_regime == "NEUTRAL"

        # -------- LOAD DATA --------
        ohlcv = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=200)
        if not ohlcv:
            continue

        candles = CandleFrame(ohlcv)

        # -------- STRATEGY --------

        impulse = generate_signal(symbol)
        if not impulse:
            continue

        # в NEUTRAL — только самые сильные импульсы
        if is_neutral and impulse.get("strength", 1) < 2:
            continue

        entry_price = validate_entry(impulse)
        if not entry_price:
            continue

        sl, tp = calc_sl_tp(entry_price, impulse)

        trade = open_trade(
            symbol=symbol,
            side=impulse["bias"],
            entry_price=entry_price,
            stop_loss=sl,
            take_profit=tp
        )

        active_trades.append(trade)
        db.save_trade(trade)
        entries += 1

        logger.info(f"ENTRY {symbol} @ {entry_price}")

        telegram.send_channel(
            f"🟢 <b>ENTRY</b>\n\n"
            f"{symbol}\n"
            f"Side: {impulse['bias']}\n"
            f"Entry: {entry_price}\n"
            f"SL: {sl:.4f}\n"
            f"TP: {tp:.4f}\n"
            f"Regime: {current_regime}"
        )

    # -------- MONITOR TRADES (SEPARATE LOOP) --------
    for trade in active_trades[:]:
        ohlcv = exchange.fetch_ohlcv(trade.pair, TIMEFRAME, limit=50)
        if not ohlcv:
            continue

        candles = CandleFrame(ohlcv).candles
        event = monitor_trade(trade, candles)

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
        f"Entries: {entries}\n"
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
        # grace period — 90 минут после старта
        if time.time() - BOT_START_TIME < 90 * 60:
            time.sleep(60)
            continue

        if time.time() - last_market_tick > WATCHDOG_TIMEOUT:
            telegram.send_admin("🛑 WATCHDOG: restarting bot")

            python = sys.executable
            subprocess.Popen([python] + sys.argv)

            os._exit(0)

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





......


import re
import asyncio
import random
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError

# ==================================================
# ================= НАСТРОЙКИ ======================
# ==================================================

API_ID = 2886532
API_HASH = "7df215535ba9bc5a9c7bb61102709403"

SESSION_NAME = "trojan_autobuy"

SOURCE_CHANNEL_ID = [
    -1003735116794,  # основной канал
    -1003101815766   # тестовый канал
]

TARGET_BOT = "@odysseus_trojanbot"

# Более "человеческие" задержки с рандомом
SEND_DELAY_MIN = 0.5
SEND_DELAY_MAX = 1.2

BUY_DELAY_MIN = 2.0      # минимум 2 секунды
BUY_DELAY_MAX = 4.0      # максимум 4 секунды

# Сколько раз пытаться нажать кнопку при редактировании
MAX_CLICK_ATTEMPTS = 3
RETRY_DELAY = 1.0        # задержка между попытками

MAX_WAIT_TIME = 20.0

LOG = "[AUTO]"

# ==================================================
# ================= REGEX ==========================
# ==================================================

SOLANA_CA_REGEX = re.compile(r"[1-9A-HJ-NP-Za-km-z]{32,44}")

# ==================================================
# ================= КЛИЕНТ ========================
# ==================================================

client = TelegramClient(
    SESSION_NAME,
    API_ID,
    API_HASH,
    device_model="Android",
    system_version="13",
    app_version="10.0",
)

# состояние
last_ca = None
waiting_for_bot_response = False
last_sent_time = 0
bot_message_id = None
buy_clicked = False
click_attempts = 0

# ==================================================
# ================= УТИЛИТЫ ========================
# ==================================================

def extract_ca(text: str | None) -> str | None:
    if not text:
        return None
    matches = SOLANA_CA_REGEX.findall(text)
    return matches[0] if matches else None

def random_delay(min_sec, max_sec):
    """Случайная задержка для эмуляции человека"""
    return random.uniform(min_sec, max_sec)

async def try_click_buy(msg, attempt=1):
    """Попытка нажать кнопку BUY с retry логикой"""
    global waiting_for_bot_response, buy_clicked, click_attempts
    
    if buy_clicked:
        return True
    
    if not msg.buttons:
        print(f"{LOG} ⚠️ Кнопки отсутствуют (попытка {attempt})")
        return False
    
    # Показываем все кнопки для отладки
    if attempt == 1:
        print(f"{LOG} 🔍 Доступные кнопки:")
        for row_idx, row in enumerate(msg.buttons):
            for btn_idx, button in enumerate(row):
                print(f"     [{row_idx}][{btn_idx}] {button.text}")
    
    for row in msg.buttons:
        for button in row:
            if button.text and "buy" in button.text.lower():
                try:
                    print(f"{LOG} 🔘 Попытка {attempt}/{MAX_CLICK_ATTEMPTS}: Нажимаю '{button.text}'")
                    
                    # Небольшая случайная задержка перед кликом (эмуляция человека)
                    await asyncio.sleep(random_delay(0.1, 0.3))
                    
                    await button.click()
                    waiting_for_bot_response = False
                    buy_clicked = True
                    print(f"{LOG} ✅ BUY успешно нажата!")
                    return True
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"{LOG} ❌ Ошибка (попытка {attempt}): {error_msg}")
                    
                    # Если это ошибка "Encrypted data invalid" - пробуем retry
                    if "encrypted data invalid" in error_msg.lower():
                        if attempt < MAX_CLICK_ATTEMPTS:
                            print(f"{LOG} 🔄 Жду {RETRY_DELAY}с перед retry...")
                            await asyncio.sleep(RETRY_DELAY)
                            
                            # Получаем свежее сообщение
                            try:
                                fresh = await client.get_messages(TARGET_BOT, ids=msg.id)
                                if fresh:
                                    return await try_click_buy(fresh, attempt + 1)
                            except Exception as e2:
                                print(f"{LOG} ❌ Ошибка получения свежего сообщения: {e2}")
                        else:
                            print(f"{LOG} 💀 Исчерпаны все попытки")
                    
                    return False
    
    print(f"{LOG} ⚠️ Кнопка BUY не найдена")
    return False

def get_channel_name(channel_id):
    if channel_id == -1003735116794:
        return "ОСНОВНОЙ"
    elif channel_id == -1003101815766:
        return "ТЕСТОВЫЙ"
    else:
        return f"ID:{channel_id}"

# ==================================================
# =============== СИГНАЛ-КАНАЛ =====================
# ==================================================

@client.on(events.NewMessage(chats=SOURCE_CHANNEL_ID))
async def signal_handler(event):
    global last_ca, waiting_for_bot_response, last_sent_time, bot_message_id, buy_clicked, click_attempts

    try:
        ca = extract_ca(event.message.text)
        if not ca:
            return

        channel_name = get_channel_name(event.chat_id)

        if ca == last_ca:
            print(f"{LOG} 🔄 [{channel_name}] CA уже обрабатывался: {ca}")
            return

        last_ca = ca
        waiting_for_bot_response = True
        bot_message_id = None
        buy_clicked = False
        click_attempts = 0
        
        print(f"\n{LOG} 🔍 [{channel_name}] Найден CA: {ca}")

        # Случайная задержка (эмуляция человека)
        delay = random_delay(SEND_DELAY_MIN, SEND_DELAY_MAX)
        print(f"{LOG} ⏳ Задержка {delay:.2f}с перед отправкой...")
        await asyncio.sleep(delay)
        
        await client.send_message(TARGET_BOT, ca)
        last_sent_time = asyncio.get_event_loop().time()
        print(f"{LOG} 📤 [{channel_name}] CA отправлен боту")

    except Exception as e:
        print(f"{LOG} ❌ Signal error: {e}")
        waiting_for_bot_response = False

# ==================================================
# ============ ОБРАБОТКА ОТВЕТА БОТА ===============
# ==================================================

@client.on(events.NewMessage(from_users=TARGET_BOT))
async def bot_new_message_handler(event):
    global waiting_for_bot_response, last_sent_time, bot_message_id

    try:
        if not waiting_for_bot_response:
            return

        current_time = asyncio.get_event_loop().time()
        if current_time - last_sent_time > MAX_WAIT_TIME:
            print(f"{LOG} ⏱️ Таймаут ожидания")
            waiting_for_bot_response = False
            return

        msg = event.message
        bot_message_id = msg.id
        
        print(f"{LOG} 📩 Новое сообщение от бота (ID: {msg.id})")
        
        # Случайная "человеческая" задержка
        delay = random_delay(BUY_DELAY_MIN, BUY_DELAY_MAX)
        print(f"{LOG} ⏳ Ожидание {delay:.2f}с перед нажатием (эмуляция человека)...")
        await asyncio.sleep(delay)
        
        # Получаем свежую версию и пробуем нажать
        fresh_msg = await client.get_messages(TARGET_BOT, ids=msg.id)
        await try_click_buy(fresh_msg)

    except FloodWaitError as e:
        print(f"{LOG} ⏳ FloodWait {e.seconds}s")
        await asyncio.sleep(e.seconds)

    except Exception as e:
        print(f"{LOG} ❌ New message error: {e}")
        waiting_for_bot_response = False


@client.on(events.MessageEdited(from_users=TARGET_BOT))
async def bot_edited_handler(event):
    global waiting_for_bot_response, bot_message_id, buy_clicked

    try:
        if not waiting_for_bot_response or buy_clicked:
            return
        
        msg = event.message
        
        if bot_message_id and msg.id == bot_message_id:
            print(f"{LOG} ✏️ Сообщение отредактировано (ID: {msg.id})")
            
            # Маленькая задержка после редактирования
            await asyncio.sleep(random_delay(0.3, 0.7))
            
            # Пробуем нажать на обновлённую кнопку
            await try_click_buy(msg)

    except Exception as e:
        print(f"{LOG} ❌ Edit handler error: {e}")

# ==================================================
# ================== ЗАПУСК ========================
# ==================================================

async def main():
    print(f"{LOG} 🚀 Запуск...")
    await client.start()
    print(f"{LOG} ✅ Telegram подключён")
    print(f"{LOG} 👀 Отслеживаем каналы:")
    print(f"     📺 ОСНОВНОЙ: -1003735116794")
    print(f"     🧪 ТЕСТОВЫЙ: -1003101815766")
    print(f"{LOG} 🤖 Бот: {TARGET_BOT}")
    print(f"{LOG} ⏱️ Задержка перед BUY: {BUY_DELAY_MIN}-{BUY_DELAY_MAX} сек (случайная)")
    print(f"{LOG} 🔄 Максимум попыток нажатия: {MAX_CLICK_ATTEMPTS}")
    print(f"{LOG} ⏳ Ожидаем сигналы...\n")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())