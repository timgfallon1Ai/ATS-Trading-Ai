from __future__ import annotations

from typing import Any, Dict, Optional

from .cross_symbol_memory import CrossSymbolMemory
from .live_feature_schema import LiveFeatureSchema
from .macro_enrichment import MacroEnrichment
from .sentiment_enrichment import SentimentEnrichment


class LiveFeatureEngine:
    """Converts UBF live ingestion payloads into feature-rich LiveFeatureSchema."""

    def __init__(
        self,
        memory: CrossSymbolMemory,
        sentiment: SentimentEnrichment,
        macro: MacroEnrichment,
    ) -> None:
        self.memory = memory
        self.sentiment = sentiment
        self.macro = macro

    # -------------------------------------------------
    # Main entry point
    # -------------------------------------------------
    def build_features(self, merged: Dict[str, Any]) -> Optional[LiveFeatureSchema]:
        symbol = merged["symbol"]

        price = merged.get("price")
        if price is None:
            return None

        tick = merged.get("tick")
        news = merged.get("news")
        tweet = merged.get("tweet")

        # Memory update
        self.memory.update(symbol, merged)

        # Spread
        bid = tick.get("bid") if tick else None
        ask = tick.get("ask") if tick else None
        spread = (ask - bid) if (ask is not None and bid is not None) else None

        # Sentiment scores
        news_score = self.sentiment.score_news(news)
        tweet_score = self.sentiment.score_tweet(tweet)

        # Macro score
        macro_score = self.macro.score(symbol, merged)

        out: LiveFeatureSchema = {
            "symbol": symbol,
            "timestamp": price["timestamp"],
            "open": float(price["open"]),
            "high": float(price["high"]),
            "low": float(price["low"]),
            "close": float(price["close"]),
            "volume": int(price["volume"]),
            "bid": bid,
            "ask": ask,
            "spread": spread,
            "news_sentiment": news_score,
            "tweet_sentiment": tweet_score,
            "macro_score": macro_score,
        }
        return out
