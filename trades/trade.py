# trades/trade.py

from datetime import datetime


class Trade:
    """
    Trade object: хранит всю информацию о сделке
    """

    def __init__(
        self,
        pair,
        direction,
        entry_price,
        stop_loss,
        take_profit,
        score=0,
        reasons=None
    ):
        self.pair = pair
        self.direction = direction  # "LONG" / "SHORT"
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.take_profit = take_profit

        self.score = score
        self.reasons = reasons or []

        self.open_time = datetime.utcnow()
        self.state = "ACTIVE"

        self.current_profit = 0.0
        self.max_profit = 0.0
        self.closed_reason = None

    # =========================================================
    # PROFIT LOGIC
    # =========================================================

    def update_profit(self, current_price):
        """
        Обновляет текущую прибыль в %
        """
        if self.direction == "LONG":
            self.current_profit = (
                (current_price - self.entry_price) / self.entry_price
            ) * 100
        else:
            self.current_profit = (
                (self.entry_price - current_price) / self.entry_price
            ) * 100

        self.max_profit = max(self.max_profit, self.current_profit)

    # =========================================================
    # EXIT CONDITIONS
    # =========================================================

    def hit_stop(self, current_price):
        """
        Проверяет, достигнут ли стоп-лосс
        """
        if self.direction == "LONG":
            return current_price <= self.stop_loss
        else:
            return current_price >= self.stop_loss

    def hit_tp(self, current_price):
        """
        Проверяет, достигнут ли тейк-профит
        """
        if self.direction == "LONG":
            return current_price >= self.take_profit
        else:
            return current_price <= self.take_profit

    # =========================================================
    # CLOSE TRADE
    # =========================================================

    def close(self, reason):
        self.state = "CLOSED"
        self.closed_reason = reason


# =========================================================
# ADAPTER: open_trade() для main.py
# =========================================================

def open_trade(symbol, side, entry_price, stop_loss, take_profit):
    """
    Универсальная функция для открытия сделки.
    Используется и в live-боте, и в backtest.
    """

    trade = Trade(
        pair=symbol,
        direction=side,
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        score=0,
        reasons=["auto"]
    )

    return trade