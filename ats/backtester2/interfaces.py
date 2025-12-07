# ats/backtester2/interfaces.py

from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterator, List, Protocol, TypedDict


# ===============================
# UBF-SHAPED BAR TYPE
# ===============================
class UBFBar(TypedDict):
    symbol: str
    timestamp: int  # epoch milliseconds
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: float
    # optional fields allowed but ignored


# ===============================
# TIME CONTEXT (BACKTEST CLOCK)
# ===============================
class TimeContext(TypedDict):
    timestamp: int  # epoch ms
    datetime: datetime  # parsed version


# ===============================
# BAR ITERATOR PROTOCOL
# Multi-symbol, time-ordered feed
# ===============================
class BarIterator(Protocol):
    def __iter__(self) -> Iterator[Dict[str, UBFBar]]:
        """Yields a dict:
            {
                "AAPL": UBFBar,
                "MSFT": UBFBar,
                ...
            }
        for every timestamp where at least one symbol has a bar.
        """
        ...


# ===============================
# BAR FEED PROTOCOL
# ===============================
class BarFeed(Protocol):
    symbols: List[str]

    def get_iterator(self) -> BarIterator: ...


# ===============================
# PORTFOLIO SNAPSHOT INTERFACE
# ===============================
class BacktestPortfolio(TypedDict):
    cash: float
    equity: float
    positions: Dict[str, float]  # symbol → size
    value: float  # cash + Σ(position * price)
