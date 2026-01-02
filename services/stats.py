# services/stats.py

from datetime import datetime, timedelta, timezone


def calculate_stats(results):
    if not results:
        return None

    wins = [r for r in results if r > 0]
    losses = [r for r in results if r <= 0]

    return {
        "trades": len(results),
        "winrate": (len(wins) / len(results)) * 100,
        "avg_return": sum(results) / len(results),
        "best": max(results),
        "worst": min(results),
    }


def daily_range():
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start.isoformat()


def weekly_range():
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=7)
    return start.isoformat()