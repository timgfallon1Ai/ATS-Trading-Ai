from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class Position:
    """
    Simple long-only position.

    - symbol: ticker
    - quantity: number of shares
    - avg_price: volume-weighted average entry price
    """

    symbol: str
    quantity: float = 0.0
    avg_price: float = 0.0


class PositionBook:
    """
    Minimal in-memory position book for backtests.

    Tracks per-symbol Position objects; does not attempt to handle
    shorts or complex multi-leg instruments in this version.
    """

    def __init__(self) -> None:
        self._positions: Dict[str, Position] = {}

    def get(self, symbol: str) -> Position:
        """Return the Position for `symbol`, creating an empty one if needed."""
        if symbol not in self._positions:
            self._positions[symbol] = Position(symbol=symbol)
        return self._positions[symbol]

    def apply_fill(self, symbol: str, qty: float, price: float) -> None:
        """
        Apply a fill to the position book.

        Long-only semantics:
        - Positive qty increases position.
        - Negative qty reduces position; if you fully close, avg_price resets.
        """
        pos = self.get(symbol)
        prev_qty = pos.quantity
        prev_avg = pos.avg_price

        new_qty = prev_qty + qty
        if new_qty == 0:
            # flat; reset
            pos.quantity = 0.0
            pos.avg_price = 0.0
            return

        if prev_qty == 0:
            # opening a new position
            pos.quantity = new_qty
            pos.avg_price = price
            return

        # update VWAP-style average price for adds
        if (prev_qty > 0 and qty > 0) or (prev_qty < 0 and qty < 0):
            total_notional = prev_qty * prev_avg + qty * price
            pos.quantity = new_qty
            pos.avg_price = total_notional / new_qty
        else:
            # partial close: quantity changes, avg price stays the same
            pos.quantity = new_qty

    def snapshot(self) -> Dict[str, Dict[str, float]]:
        """Return a JSON-serializable view of all positions."""
        return {
            sym: {"quantity": p.quantity, "avg_price": p.avg_price}
            for sym, p in self._positions.items()
        }
