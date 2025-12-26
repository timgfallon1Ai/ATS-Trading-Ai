from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional, Protocol

import requests

from .types import PriceTick


class MarketDataProvider(Protocol):
    """Minimal interface for polling market data."""

    def get_last_trade(self, symbol: str) -> PriceTick: ...


@dataclass
class PolygonMarketData:
    """Polygon 'last trade' REST polling provider.

    Requires POLYGON_API_KEY in the environment (recommended) or passed in.
    """

    api_key: Optional[str] = None
    timeout_seconds: float = 10.0
    session: Optional[requests.Session] = None

    def __post_init__(self) -> None:
        if self.session is None:
            self.session = requests.Session()

    def get_last_trade(self, symbol: str) -> PriceTick:
        import os

        api_key = self.api_key or os.getenv("POLYGON_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Polygon API key not set. Set POLYGON_API_KEY env var (preferred) "
                "or pass api_key=... to PolygonMarketData."
            )

        url = f"https://api.polygon.io/v2/last/trade/{symbol}"
        resp = self.session.get(
            url, params={"apiKey": api_key}, timeout=self.timeout_seconds
        )
        resp.raise_for_status()
        data = resp.json()

        # Polygon response expected: {"results": {"p": <price>, "t": <ns epoch>, ...}, ...}
        results = data.get("results") or {}
        price = float(results["p"])
        ts_ns = int(results["t"])
        ts = datetime.fromtimestamp(ts_ns / 1e9, tz=timezone.utc)

        return PriceTick(
            symbol=symbol, price=price, timestamp=ts, source="polygon:last_trade"
        )


@dataclass
class StaticMarketData:
    """In-memory deterministic provider useful for tests and demos."""

    prices: Dict[str, float]
    source: str = "static"

    def get_last_trade(self, symbol: str) -> PriceTick:
        px = float(self.prices[symbol])
        return PriceTick(
            symbol=symbol,
            price=px,
            timestamp=datetime.now(tz=timezone.utc),
            source=self.source,
        )
