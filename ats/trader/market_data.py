from __future__ import annotations

from typing import Dict, Optional


class MarketData:
    """
    Minimal market data holder for the Trader.

    - Live trading: prices are injected from feeds.
    - Backtesting: prices are injected by the backtest engine.
    """

    def __init__(self) -> None:
        self._prices: Dict[str, float] = {}

    def update(self, prices: Dict[str, float]) -> None:
        """Merge new prices into the current snapshot."""
        self._prices.update(prices)

    def get_price(self, symbol: str) -> Optional[float]:
        """Return the latest price for `symbol`, or None if unknown."""
        return self._prices.get(symbol)

    @property
    def snapshot(self) -> Dict[str, float]:
        """Return a shallow copy of the current price map."""
        return dict(self._prices)
