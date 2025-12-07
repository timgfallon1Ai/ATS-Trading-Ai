from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from ats.trader.fill_types import Fill


@dataclass
class Portfolio:
    """
    Simple long-only portfolio model.

    Tracks:
    - starting_capital
    - cash
    - per-symbol positions
    - per-symbol average entry prices
    - realized PnL
    """

    starting_capital: float = 1000.0
    cash: float = field(init=False)
    positions: Dict[str, float] = field(default_factory=dict)
    avg_price: Dict[str, float] = field(default_factory=dict)
    realized_pnl: float = 0.0

    def __post_init__(self) -> None:
        self.cash = float(self.starting_capital)

    # ------------------------------------------------------------------ #
    # Fills / PnL
    # ------------------------------------------------------------------ #
    def apply_fill(self, fill: Fill) -> float:
        """
        Apply a fill to the portfolio and return the realized PnL
        associated with this fill.

        Assumes long-only semantics:
        - BUY increases position and reduces cash.
        - SELL reduces position, realizes PnL vs avg_price, increases cash.
        """
        symbol = fill.symbol
        side = fill.side.lower()
        size = float(fill.size)
        price = float(fill.price)

        if size <= 0:
            raise ValueError("Fill.size must be positive")

        pos = self.positions.get(symbol, 0.0)

        if side == "buy":
            cost = price * size
            self.cash -= cost

            new_pos = pos + size
            prev_cost = self.avg_price.get(symbol, 0.0) * pos
            new_cost = prev_cost + cost

            self.positions[symbol] = new_pos
            self.avg_price[symbol] = new_cost / new_pos if new_pos else 0.0

            realized_pnl = 0.0

        elif side == "sell":
            exit_value = price * size
            self.cash += exit_value

            entry_price = self.avg_price.get(symbol, price)
            realized_pnl = (price - entry_price) * size
            self.realized_pnl += realized_pnl

            new_pos = pos - size
            self.positions[symbol] = new_pos
            if new_pos <= 0:
                self.avg_price.pop(symbol, None)

        else:
            raise ValueError("Fill.side must be 'buy' or 'sell'")

        return realized_pnl

    # ------------------------------------------------------------------ #
    # Equity & snapshots
    # ------------------------------------------------------------------ #
    def equity(self, market_prices: Dict[str, float]) -> float:
        """Return total equity = cash + unrealized PnL."""
        unrealized = 0.0
        for sym, qty in self.positions.items():
            price = market_prices.get(sym)
            if price is None:
                # no quote → assume zero contribution for now
                continue
            cost = self.avg_price.get(sym, price)
            unrealized += (price - cost) * qty
        return self.cash + unrealized

    def snapshot(self, market_prices: Dict[str, float]) -> Dict[str, Any]:
        """
        Return a JSON-serializable snapshot of the portfolio.
        """
        return {
            "starting_capital": self.starting_capital,
            "cash": self.cash,
            "positions": dict(self.positions),
            "avg_price": dict(self.avg_price),
            "realized_pnl": self.realized_pnl,
            "equity": self.equity(market_prices),
        }
