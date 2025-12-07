from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class Position:
    size: float = 0.0
    avg_price: float = 0.0


class LivePositionBook:
    """Maintains live positions for each symbol."""

    def __init__(self):
        self.positions: Dict[str, Position] = {}

    def apply_fill(self, symbol: str, size_delta: float, price: float) -> None:
        pos = self.positions.get(symbol, Position())

        new_size = pos.size + size_delta
        if new_size == 0:
            self.positions[symbol] = Position(0.0, 0.0)
            return

        if pos.size == 0:
            avg = price
        else:
            avg = (pos.avg_price * pos.size + price * size_delta) / new_size

        self.positions[symbol] = Position(new_size, avg)

    def get(self, symbol: str) -> Position:
        return self.positions.get(symbol, Position())
