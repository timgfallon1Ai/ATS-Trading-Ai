# ats/backtester2/portfolio_sync.py

from __future__ import annotations

from typing import Any, Dict

from ats.backtester2.portfolio_sim import PortfolioSimulator
from ats.backtester2.position_book_bt import PositionBookBT


class PortfolioSync:
    """Maintains coherence between:
        - PositionBookBT (positions)
        - PortfolioSimulator (equity, cash)
        - Ledger (pnl, trade history)

    Backtester2 calls this after fills and MTM updates.
    """

    def __init__(
        self, position_book: PositionBookBT, portfolio_sim: PortfolioSimulator
    ):
        self.position_book = position_book
        self.portfolio = portfolio_sim

    def apply_fills(self, fills):
        """Push newly executed trades into the position book & cash balance."""
        for fill in fills:
            symbol = fill["symbol"]
            qty = float(fill["qty"])
            price = float(fill["price"])

            # Update position book
            self.position_book.apply_fill(fill)

            # Cash is reduced when buying, increased when selling
            cash_change = -qty * price
            self.portfolio.apply_cash_change(cash_change)

    def mark_to_market(self, bar_prices: Dict[str, Any], timestamp: int):
        """Revalue positions + update equity."""
        self.portfolio.mark_to_market(
            positions=self.position_book.positions,
            slices=bar_prices,
            timestamp=timestamp,
        )
