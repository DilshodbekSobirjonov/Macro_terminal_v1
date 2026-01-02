# trades/exits.py

def calc_sl_tp(entry_price, impulse):
    """
    ATR-based SL / TP
    """
    atr = impulse["atr"]

    # LONG only (как сейчас в стратегии)
    sl = impulse["impulse_low"] - atr * 0.6
    tp = entry_price + (entry_price - sl) * 2

    return sl, tp
