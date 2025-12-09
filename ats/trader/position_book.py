from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class Position:
    """Simple long-only position."""

    symbol: str
    quantity: float = 0.0
    avg_price: float = 0.0


class PositionBook:
    """Tracks per-symbol positions for the portfolio."""

    def __init__(self) -> None:
        self._positions: Dict[str, Position] = {}

    def get(self, symbol: str) -> Position:
        """Return the Position for `symbol`, creating an empty one if needed."""
        if symbol not in self._positions:
            self._positions[symbol] = Position(symbol=symbol)
        return self._positions[symbol]

    def all(self) -> Dict[str, Position]:
        """Return a mapping of symbol → Position."""
        return dict(self._positions)
