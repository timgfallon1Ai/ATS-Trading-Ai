from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class Position:
    size: float = 0.0
    avg_price: float = 0.0

    def update_with_fill(self, side: str, size: float, price: float):
        if side == "buy":
            new_cost = self.avg_price * self.size + price * size
            self.size += size
            self.avg_price = new_cost / self.size
        else:
            self.size -= size
            if self.size == 0:
                self.avg_price = 0.0


class PositionBook:
    def __init__(self):
        self.positions: Dict[str, Position] = {}

    def get(self, symbol: str) -> Position:
        if symbol not in self.positions:
            self.positions[symbol] = Position()
        return self.positions[symbol]
