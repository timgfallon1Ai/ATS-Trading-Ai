from __future__ import annotations

from typing import Dict


class MarketData:
    """In-memory snapshot of latest prices per symbol."""

    def __init__(self) -> None:
        self._prices: Dict[str, float] = {}

    def update(self, prices: Dict[str, float]) -> None:
        """Merge a partial price update into the snapshot."""
        for symbol, price in prices.items():
            self._prices[symbol] = float(price)

    def price(self, symbol: str) -> float:
        """Return the last known price for `symbol`."""
        if symbol not in self._prices:
            raise KeyError(f"No price available for symbol {symbol!r}")
        return self._prices[symbol]

    def snapshot(self) -> Dict[str, float]:
        """Return a shallow copy of the price snapshot."""
        return dict(self._prices)
