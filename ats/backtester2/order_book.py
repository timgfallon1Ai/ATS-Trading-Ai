# ats/backtester2/order_book.py

from __future__ import annotations

from typing import Tuple


class OrderBook:
    """Minimal deterministic bid/ask simulator for backtests.

    Uses OHLC to create synthetic quotes:
        best_bid = open * (1 - 0.0001)
        best_ask = open * (1 + 0.0001)

    This avoids randomness but preserves spread behavior.
    """

    def __init__(self, spread_bps: float = 1.0):
        self.spread_bps = spread_bps / 10000  # convert bps → fraction

    def get_best_quotes(self, symbol: str) -> Tuple[float, float]:
        """This method is overridden by passing bar data directly.
        The ExecutionEngine will pass the correct open price.
        """
        raise RuntimeError(
            "OrderBook.get_best_quotes(symbol) must be called via "
            "provide_quotes() during execution."
        )

    def provide_quotes(self, symbol: str, open_price: float) -> Tuple[float, float]:
        """Given the bar's open price, synthesizes bid/ask."""
        bid = open_price * (1 - self.spread_bps)
        ask = open_price * (1 + self.spread_bps)
        return bid, ask
