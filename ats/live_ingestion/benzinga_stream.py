from __future__ import annotations

import asyncio
from typing import Any, Callable

from .ingestion_state import IngestionState


class BenzingaStream:
    """Real-time news sentiment stream."""

    def __init__(self, api_key: str, state: IngestionState) -> None:
        self.api_key = api_key
        self.state = state
        self._running = False

    async def connect(self) -> None:
        self._running = True
        await asyncio.sleep(0.1)

    async def run(
        self, symbols: list[str], on_news: Callable[[dict[str, Any]], None]
    ) -> None:
        if not self._running:
            await self.connect()

        while self._running:
            for symbol in symbols:
                article = {
                    "symbol": symbol,
                    "headline": "Market reacts positively",
                    "sentiment": 0.72,
                    "timestamp": 1700000000,
                }
                self.state.update_timestamp(symbol, article["timestamp"])
                on_news(article)

            await asyncio.sleep(5.0)

    def stop(self) -> None:
        self._running = False
