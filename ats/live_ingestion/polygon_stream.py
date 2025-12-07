from __future__ import annotations

import asyncio
from typing import Any, Callable

from .ingestion_state import IngestionState


class PolygonStream:
    """Live connection to Polygon.io WebSocket streaming API.
    Normalized 1-minute bars get forwarded through callback.
    """

    def __init__(self, api_key: str, state: IngestionState) -> None:
        self.api_key = api_key
        self.state = state
        self._running = False

    async def connect(self) -> None:
        self._running = True
        await asyncio.sleep(0.1)  # simulate connect
        # In real implementation: open WS -> authenticate

    async def run(
        self, symbols: list[str], on_bar: Callable[[dict[str, Any]], None]
    ) -> None:
        if not self._running:
            await self.connect()

        # Simulated loop
        while self._running:
            for symbol in symbols:
                bar = {
                    "symbol": symbol,
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.5,
                    "close": 100.5,
                    "volume": 123450,
                    "timestamp": 1700000000,
                }
                self.state.update_timestamp(symbol, bar["timestamp"])
                on_bar(bar)

            await asyncio.sleep(1.0)

    def stop(self) -> None:
        self._running = False
