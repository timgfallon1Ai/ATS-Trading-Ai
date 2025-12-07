from typing import List

from .schema import Bar


def normalize_bars(bars: List[Bar]) -> List[Bar]:
    """Apply deterministic normalization to ensure stable features.

    Rules:
    - prices must be > 0
    - volume must be >= 0
    - if high/low reversed, fix automatically
    """
    normalized = []

    for b in bars:
        high = max(b.high, b.low)
        low = min(b.high, b.low)

        price_floor = 0.0001

        n = Bar(
            timestamp=b.timestamp,
            open=max(price_floor, b.open),
            high=max(price_floor, high),
            low=max(price_floor, low),
            close=max(price_floor, b.close),
            volume=max(0.0, b.volume),
            vwap=b.vwap,
            sentiment=b.sentiment,
            news_impact=b.news_impact,
            volatility=b.volatility,
            symbol=b.symbol,
            extra=b.extra,
        )

        normalized.append(n)

    return normalized
