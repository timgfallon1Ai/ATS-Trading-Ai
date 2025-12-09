from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from .fill_types import Fill
from .position_book import Position, PositionBook


@dataclass
class Portfolio:
    """
    Simple long-only portfolio.

    Tracks:
    - cash
    - realized_pnl
    - positions
    """

    starting_cash: float = 100_000.0
    cash: float = field(init=False)
    realized_pnl: float = field(init=False)
    positions: PositionBook = field(init=False)

    def __post_init__(self) -> None:
        self.cash = float(self.starting_cash)
        self.realized_pnl = 0.0
        self.positions = PositionBook()

    # ------------------------------------------------------------------ #
    # Fill application
    # ------------------------------------------------------------------ #

    def apply_fill(self, fill: Fill) -> None:
        """Update cash, positions, and realized PnL for a single fill."""
        pos = self.positions.get(fill.symbol)

        if fill.side == "buy":
            # Opening or adding to a long position
            total_qty = pos.quantity + fill.size
            if total_qty <= 0:
                # Strange edge case; treat as flat
                pos.quantity = 0.0
                pos.avg_price = 0.0
            else:
                total_cost = pos.quantity * pos.avg_price + fill.size * fill.price
                pos.quantity = total_qty
                pos.avg_price = total_cost / total_qty

            self.cash -= fill.size * fill.price

        else:  # sell
            if pos.quantity <= 0:
                # Selling when flat or short is unsupported in this simple model.
                raise ValueError(
                    f"Cannot sell {fill.size} of {fill.symbol} with quantity {pos.quantity}"
                )

            if fill.size > pos.quantity:
                raise ValueError(
                    f"Sell size {fill.size} exceeds position quantity {pos.quantity}"
                )

            # Realized PnL = (sell price - avg_price) * quantity sold
            pnl = (fill.price - pos.avg_price) * fill.size
            self.realized_pnl += pnl

            pos.quantity -= fill.size
            self.cash += fill.size * fill.price

            if pos.quantity == 0:
                pos.avg_price = 0.0

    def apply_fills(self, fills: list[Fill]) -> None:
        """Apply a batch of fills."""
        for fill in fills:
            self.apply_fill(fill)

    # ------------------------------------------------------------------ #
    # Valuation
    # ------------------------------------------------------------------ #

    def equity(self, prices: Dict[str, float]) -> float:
        """Return total equity = cash + sum(quantity * price)."""
        value = self.cash
        for symbol, pos in self.positions.all().items():
            if pos.quantity == 0:
                continue
            px = prices.get(symbol, pos.avg_price)
            value += pos.quantity * px
        return value

    # ------------------------------------------------------------------ #
    # Serialization
    # ------------------------------------------------------------------ #

    def snapshot(self, prices: Dict[str, float]) -> Dict[str, object]:
        """Return a JSON-serializable snapshot of portfolio state."""
        positions = {
            symbol: {
                "quantity": pos.quantity,
                "avg_price": pos.avg_price,
            }
            for symbol, pos in self.positions.all().items()
            if pos.quantity != 0
        }

        equity = self.equity(prices)

        return {
            "cash": self.cash,
            "realized_pnl": self.realized_pnl,
            "equity": equity,
            "positions": positions,
        }
