# core/universe.py

def filter_symbols(
    tickers,
    min_volume_usd=50_000_000,
    min_atr_percent=0.5,
    max_symbols=20
):
    """
    tickers: dict from exchange.fetch_tickers()
    """

    candidates = []

    for symbol, data in tickers.items():
        if not symbol.endswith("USDT"):
            continue

        if "PERP" in symbol:
            continue

        volume = data.get("quoteVolume", 0)
        high = data.get("high", 0)
        low = data.get("low", 0)
        last = data.get("last", 0)

        if not volume or not high or not low or not last:
            continue

        atr_percent = ((high - low) / last) * 100

        if volume >= min_volume_usd and atr_percent >= min_atr_percent:
            candidates.append((symbol, volume, atr_percent))

    # сортируем по объёму
    candidates.sort(key=lambda x: x[1], reverse=True)

    return [c[0] for c in candidates[:max_symbols]]