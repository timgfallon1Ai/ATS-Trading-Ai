from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Bar:
    """Minimal OHLCV bar used by Backtester2.

    Notes:
        - timestamp is an ISO-8601 string (e.g. "2025-01-01T09:30:00").
        - symbol is the tradable (e.g. "AAPL").
        - volume is included for completeness, but is not required by the core engine.
    """

    timestamp: str
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float
