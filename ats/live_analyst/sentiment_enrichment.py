from __future__ import annotations

from typing import Any, Dict, Optional


class SentimentEnrichment:
    """Converts raw Benzinga & Twitter payloads into
    normalized float sentiment scores.
    """

    def score_news(self, article: Optional[Dict[str, Any]]) -> Optional[float]:
        if not article:
            return None
        return float(article.get("sentiment", 0.0))

    def score_tweet(self, tweet: Optional[Dict[str, Any]]) -> Optional[float]:
        if not tweet:
            return None
        return float(tweet.get("sentiment", 0.0))
