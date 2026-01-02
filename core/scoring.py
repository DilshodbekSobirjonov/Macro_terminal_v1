# core/scoring.py

from core.structure import MarketStructure
from core.indicators import (
    atr_regime,
    volume_anomaly,
    oi_delta_positive
)


class SignalScore:
    def __init__(self):
        self.score = 0
        self.reasons = []

    def add(self, points, reason):
        self.score += points
        self.reasons.append(reason)


def calculate_score(candles):
    """
    Возвращает (score, reasons)
    """
    score = SignalScore()

    structure = MarketStructure(candles)

    # 1️⃣ Structure (основа)
    if structure.detect_choch():
        score.add(3, "CHoCH detected")

    if structure.detect_bos():
        score.add(2, "BOS confirmed")

    # 2️⃣ ATR regime
    atr_state = atr_regime(candles)
    if atr_state == "expansion":
        score.add(1, "ATR expansion")
    elif atr_state == "overheated":
        score.add(-2, "ATR overheated")

    # 3️⃣ Volume
    if volume_anomaly(candles):
        score.add(1, "Volume anomaly")

    # 4️⃣ Open Interest
    if oi_delta_positive(candles):
        score.add(1, "OI increasing")

    return score.score, score.reasons
