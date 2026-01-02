# trades/trade.py

from datetime import datetime


class Trade:
    def __init__(
        self,
        pair,
        direction,
        entry_price,
        score,
        reasons,
        tp_levels,
        sl_percent
    ):
        self.pair = pair
        self.direction = direction  # "LONG" / "SHORT"
        self.entry_price = entry_price
        self.score = score
        self.reasons = reasons

        self.tp_levels = tp_levels
        self.sl_percent = sl_percent

        self.open_time = datetime.utcnow()
        self.state = "ACTIVE"

        self.max_profit = 0.0
        self.current_profit = 0.0
        self.closed_reason = None

    def update_profit(self, current_price):
        if self.direction == "LONG":
            self.current_profit = (
                (current_price - self.entry_price) / self.entry_price
            ) * 100
        else:
            self.current_profit = (
                (self.entry_price - current_price) / self.entry_price
            ) * 100

        self.max_profit = max(self.max_profit, self.current_profit)

    def hit_stop(self):
        return self.current_profit <= -self.sl_percent

    def hit_tp(self):
        for tp in self.tp_levels:
            if self.current_profit >= tp:
                return tp
        return None

    def close(self, reason):
        self.state = "CLOSED"
        self.closed_reason = reason
