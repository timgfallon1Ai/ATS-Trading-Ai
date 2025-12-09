from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Side = Literal["buy", "sell"]


@dataclass
class Bar:
    """
    Minimal OHLCV bar used by the backtester.

    - timestamp: ISO 8601 string (e.g. "2025-12-02T09:30:00Z").
    - symbol: Trading symbol (e.g. "AAPL").
    - open/high/low/close: Bar prices.
    - volume: Optional, for now we don't enforce or use it heavily.
    """

    timestamp: str
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
