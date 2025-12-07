# ats/backtester2/slippage_model.py

from __future__ import annotations


class SlippageModel:
    """Simple market-impact model.

    Applies slippage proportional to order size.
    """

    def __init__(self, impact_bps_per_100_shares: float = 2.0):
        self.impact = impact_bps_per_100_shares / 10000

    def apply(
        self, symbol: str, qty: int, price: float, best_bid: float, best_ask: float
    ) -> float:
        """Buys execute near ask, sells near bid.
        Add size-based slippage on top.
        """
        if qty > 0:
            base = best_ask
        else:
            base = best_bid

        impact = abs(qty) / 100 * self.impact
        return base * (1 + impact)
