from __future__ import annotations

import asyncio
from typing import Any, Callable

from .ingestion_state import IngestionState


class TwitterStream:
    """Streams tweet sentiment related to stock symbols."""

    def __init__(self, api_bearer: str, state: IngestionState) -> None:
        self.api_bearer = api_bearer
        self.state = state
        self._running = False

    async def connect(self) -> None:
        self._running = True
        await asyncio.sleep(0.1)

    async def run(
        self, symbols: list[str], on_tweet: Callable[[dict[str, Any]], None]
    ) -> None:
        if not self._running:
            await self.connect()

        while self._running:
            for symbol in symbols:
                tweet = {
                    "symbol": symbol,
                    "text": "Bullish sentiment rising.",
                    "sentiment": 0.68,
                    "timestamp": 1700000000,
                }
                self.state.update_timestamp(symbol, tweet["timestamp"])
                on_tweet(tweet)

            await asyncio.sleep(2.0)

    def stop(self) -> None:
        self._running = False
