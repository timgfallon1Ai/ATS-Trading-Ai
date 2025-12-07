from __future__ import annotations

from typing import Optional, TypedDict


class LiveFeatureSchema(TypedDict):
    """Unified live feature schema emitted by LiveFeatureEngine.

    This schema feeds the 12-strategy unified LiveStrategyAdapter.
    """

    symbol: str
    timestamp: int

    # Price features
    open: float
    high: float
    low: float
    close: float
    volume: int

    # Tick-level enhancements (from IBKR)
    bid: Optional[float]
    ask: Optional[float]
    spread: Optional[float]

    # Sentiment feeds
    news_sentiment: Optional[float]
    tweet_sentiment: Optional[float]

    # Macro enrichment
    macro_score: Optional[float]
