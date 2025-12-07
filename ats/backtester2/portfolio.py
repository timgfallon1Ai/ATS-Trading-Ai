from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

# ============================================================
#  SNAPSHOT
# ============================================================


@dataclass
class PortfolioSnapshot:
    timestamp: int
    cash: float
    equity: float
    positions: Dict[str, float]  # symbol → quantity
    prices: Dict[str, float]  # symbol → last_close_price

    @property
    def total_value(self) -> float:
        return self.cash + self.equity


# ============================================================
#  POSITION BOOK
# ============================================================


@dataclass
class Position:
    qty: float = 0.0
    last_price: float = 0.0

    def market_value(self) -> float:
        return self.qty * self.last_price


class PositionBook:
    """Unified position ledger for:
        - Backtester2
        - Live Trader
        - Replay/Inspector

    Maintains:
        - symbol → Position
        - MTM marking
    """

    def __init__(self):
        self.positions: Dict[str, Position] = {}

    # ------------------------------------------------------------
    #  POSITION UPDATES
    # ------------------------------------------------------------
    def update_position(self, symbol: str, qty_change: float, price: float) -> None:
        """Applies a filled order at a given price."""
        if symbol not in self.positions:
            self.positions[symbol] = Position()

        pos = self.positions[symbol]
        pos.qty += qty_change
        pos.last_price = price

        # auto-delete fully closed positions
        if abs(pos.qty) < 1e-12:
            del self.positions[symbol]

    # ------------------------------------------------------------
    #  MARK TO MARKET
    # ------------------------------------------------------------
    def mark_to_market(self, price_map: Dict[str, float]) -> None:
        """MTM updates all held positions using last-close prices."""
        for symbol, pos in self.positions.items():
            if symbol in price_map:
                pos.last_price = price_map[symbol]

    # ------------------------------------------------------------
    #  SNAPSHOTS
    # ------------------------------------------------------------
    def snapshot(self, timestamp: int, cash: float) -> PortfolioSnapshot:
        """Returns a full point-in-time portfolio snapshot."""
        prices = {s: p.last_price for s, p in self.positions.items()}
        equity = sum(p.market_value() for p in self.positions.values())

        return PortfolioSnapshot(
            timestamp=timestamp,
            cash=cash,
            equity=equity,
            positions={s: p.qty for s, p in self.positions.items()},
            prices=prices,
        )
