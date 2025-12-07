from __future__ import annotations

from typing import Any, Dict, Optional


class UnifiedLiveBarBuilder:
    """Combines:
    - Polygon price bars
    - IBKR ticks
    - Benzinga news sentiment
    - Twitter sentiment

    Produces a unified real-time feature-ready bar.
    """

    def __init__(self) -> None:
        self._cache: Dict[str, Dict[str, Any]] = {}

    def update_polygon(self, bar: dict[str, Any]) -> None:
        symbol = bar["symbol"]
        self._ensure(symbol)
        self._cache[symbol]["price"] = bar

    def update_ibkr(self, tick: dict[str, Any]) -> None:
        symbol = tick["symbol"]
        self._ensure(symbol)
        self._cache[symbol]["tick"] = tick

    def update_news(self, article: dict[str, Any]) -> None:
        symbol = article["symbol"]
        self._ensure(symbol)
        self._cache[symbol]["news"] = article

    def update_tweet(self, tweet: dict[str, Any]) -> None:
        symbol = tweet["symbol"]
        self._ensure(symbol)
        self._cache[symbol]["tweet"] = tweet

    def build(self, symbol: str) -> Optional[dict[str, Any]]:
        if symbol not in self._cache:
            return None

        data = self._cache[symbol]
        if "price" not in data:
            return None

        out = {
            "symbol": symbol,
            "timestamp": data["price"]["timestamp"],
            "price": data["price"],
            "tick": data.get("tick"),
            "news": data.get("news"),
            "tweet": data.get("tweet"),
        }
        return out

    def _ensure(self, symbol: str) -> None:
        if symbol not in self._cache:
            self._cache[symbol] = {}
