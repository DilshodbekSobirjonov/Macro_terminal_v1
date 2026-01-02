# core/regime.py

from core.indicators import atr_regime


def ema(values, period):
    k = 2 / (period + 1)
    ema_val = values[0]
    for v in values[1:]:
        ema_val = v * k + ema_val * (1 - k)
    return ema_val


def btc_trend(candles):
    """
    Определяет направление тренда BTC по EMA50 / EMA200
    """
    closes = [c.close for c in candles]

    if len(closes) < 200:
        return None

    ema50 = ema(closes[-50:], 50)
    ema200 = ema(closes[-200:], 200)

    if ema50 > ema200:
        return "BULL"
    else:
        return "BEAR"


def market_regime(btc_candles):
    """
    Возвращает:
    - RISK_ON
    - NEUTRAL
    - RISK_OFF
    """

    # защита от малого количества данных
    if len(btc_candles) < 220:
        return "RISK_OFF"

    trend = btc_trend(btc_candles)
    atr_state = atr_regime(btc_candles)

    # -------------------------------
    # 🔴 RISK_OFF — защита капитала
    # -------------------------------
    if trend == "BEAR":
        return "RISK_OFF"

    if atr_state == "overheated":
        return "RISK_OFF"

    # -------------------------------
    # 🟢 RISK_ON — можно рисковать
    # -------------------------------
    if trend == "BULL" and atr_state == "expansion":
        return "RISK_ON"

    # -------------------------------
    # 🟡 NEUTRAL — торгуем аккуратно
    # -------------------------------
    return "NEUTRAL"