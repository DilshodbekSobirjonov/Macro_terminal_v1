# services/db.py

import sqlite3
from datetime import datetime
from trades.trade import Trade


class Database:
    def __init__(self, path="macro_terminal.db"):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self._create_tables()

    def _create_tables(self):
        cur = self.conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pair TEXT,
            direction TEXT,
            entry_price REAL,
            score INTEGER,
            reasons TEXT,
            tp_levels TEXT,
            sl_percent REAL,
            state TEXT,
            open_time TEXT,
            close_time TEXT,
            result REAL,
            closed_reason TEXT
        )
        """)

        self.conn.commit()

    # ---------- SAVE ----------

    def save_trade(self, trade: Trade):
        cur = self.conn.cursor()

        cur.execute("""
        INSERT INTO trades (
            pair, direction, entry_price, score, reasons,
            tp_levels, sl_percent, state, open_time
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade.pair,
            trade.direction,
            trade.entry_price,
            trade.score,
            ",".join(trade.reasons),
            ",".join(map(str, trade.tp_levels)),
            trade.sl_percent,
            trade.state,
            trade.open_time.isoformat()
        ))

        self.conn.commit()

    # ---------- UPDATE ----------

    def close_trade(self, trade: Trade):
        cur = self.conn.cursor()

        cur.execute("""
        UPDATE trades
        SET state = ?, close_time = ?, result = ?, closed_reason = ?
        WHERE pair = ? AND state = 'ACTIVE'
        """, (
            "CLOSED",
            datetime.utcnow().isoformat(),
            trade.current_profit,
            trade.closed_reason,
            trade.pair
        ))

        self.conn.commit()

    # ---------- LOAD ----------

    def load_active_trades(self):
        cur = self.conn.cursor()

        cur.execute("""
        SELECT pair, direction, entry_price, score, reasons,
               tp_levels, sl_percent
        FROM trades
        WHERE state = 'ACTIVE'
        """)

        trades = []
        for row in cur.fetchall():
            trade = Trade(
                pair=row[0],
                direction=row[1],
                entry_price=row[2],
                score=row[3],
                reasons=row[4].split(","),
                tp_levels=list(map(float, row[5].split(","))),
                sl_percent=row[6]
            )
            trades.append(trade)

        return trades