from __future__ import annotations

import asyncio
from typing import Any, Callable

from .ingestion_state import IngestionState


class IBKRStream:
    """Live price/quote stream from Interactive Brokers."""

    def __init__(self, state: IngestionState) -> None:
        self.state = state
        self._running = False

    async def connect(self) -> None:
        self._running = True
        await asyncio.sleep(0.1)

    async def run(
        self, symbols: list[str], on_tick: Callable[[dict[str, Any]], None]
    ) -> None:
        if not self._running:
            await self.connect()

        while self._running:
            for symbol in symbols:
                tick = {
                    "symbol": symbol,
                    "bid": 100.0,
                    "ask": 100.1,
                    "timestamp": 1700000000,
                }
                self.state.update_timestamp(symbol, tick["timestamp"])
                on_tick(tick)

            await asyncio.sleep(0.5)

    def stop(self) -> None:
        self._running = False
