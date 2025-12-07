from __future__ import annotations

from typing import Any, Callable

from .benzinga_stream import BenzingaStream
from .ibkr_stream import IBKRStream
from .ingestion_state import IngestionState
from .polygon_stream import PolygonStream
from .symbol_subscription_manager import SymbolSubscriptionManager
from .twitter_stream import TwitterStream
from .unified_live_bar_builder import UnifiedLiveBarBuilder


class IngestionRouter:
    """Manages all live streams and forwards normalized output
    to the unified live bar builder.
    """

    def __init__(
        self, polygon_key: str, benzinga_key: str, twitter_bearer: str
    ) -> None:

        self.state = IngestionState()
        self.subs = SymbolSubscriptionManager()

        self.polygon = PolygonStream(polygon_key, self.state)
        self.benzinga = BenzingaStream(benzinga_key, self.state)
        self.twitter = TwitterStream(twitter_bearer, self.state)
        self.ibkr = IBKRStream(self.state)

        self.ubf = UnifiedLiveBarBuilder()

    async def start_all(self, callback: Callable[[dict[str, Any]], None]) -> None:
        """Runs all providers concurrently."""
        import asyncio

        async def polygon_task():
            await self.polygon.run(
                self.subs.polygon_list(),
                lambda bar: self._handle_polygon(bar, callback),
            )

        async def ibkr_task():
            await self.ibkr.run(
                self.subs.ibkr_list(), lambda tick: self._handle_ibkr(tick, callback)
            )

        async def news_task():
            await self.benzinga.run(
                self.subs.benzinga_list(),
                lambda news: self._handle_news(news, callback),
            )

        async def twitter_task():
            await self.twitter.run(
                self.subs.twitter_list(), lambda tw: self._handle_tweet(tw, callback)
            )

        await asyncio.gather(polygon_task(), ibkr_task(), news_task(), twitter_task())

    # ----------------------------
    # Internal handlers
    # ----------------------------
    def _handle_polygon(self, bar: dict[str, Any], cb: Callable) -> None:
        self.ubf.update_polygon(bar)
        merged = self.ubf.build(bar["symbol"])
        if merged:
            cb(merged)

    def _handle_ibkr(self, tick: dict[str, Any], cb: Callable) -> None:
        self.ubf.update_ibkr(tick)
        merged = self.ubf.build(tick["symbol"])
        if merged:
            cb(merged)

    def _handle_news(self, news: dict[str, Any], cb: Callable) -> None:
        self.ubf.update_news(news)
        merged = self.ubf.build(news["symbol"])
        if merged:
            cb(merged)

    def _handle_tweet(self, tw: dict[str, Any], cb: Callable) -> None:
        self.ubf.update_tweet(tw)
        merged = self.ubf.build(tw["symbol"])
        if merged:
            cb(merged)
