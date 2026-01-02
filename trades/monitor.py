# trades/monitor.py

from core.structure import MarketStructure
from core.indicators import volume_anomaly, oi_delta_positive


def monitor_trade(trade, candles):
    """
    Проверяет состояние сделки и возвращает событие
    """
    last_candle = candles[-1]
    trade.update_profit(last_candle.close)

    structure = MarketStructure(candles)

    # ❌ Stop Loss
    if trade.hit_stop():
        trade.close("Stop loss")
        return "STOP"

    # 🎯 Take Profit
    tp_hit = trade.hit_tp()
    if tp_hit:
        return f"TP +{tp_hit}%"

    # ⚠️ Логическое закрытие
    if trade.direction == "LONG":
        if structure.detect_choch():
            trade.close("Structure reversed (CHoCH)")
            return "LOGIC CLOSE"

        if not volume_anomaly(candles) and not oi_delta_positive(candles):
            trade.close("Interest faded")
            return "LOGIC CLOSE"

    return None
