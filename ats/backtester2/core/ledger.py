# ats/backtester2/core/ledger.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .bar import Bar


@dataclass
class Position:
    symbol: str
    quantity: float = 0.0
    avg_price: float = 0.0

    def update(self, fill_price: float, fill_qty: float) -> None:
        """Standard average-price position updating."""
        new_qty = self.quantity + fill_qty

        # Closing or reducing position
        if self.quantity != 0 and (
            self.quantity > 0 > fill_qty or self.quantity < 0 < fill_qty
        ):
            realized = min(abs(self.quantity), abs(fill_qty))
            # avg price remains unchanged on partial close
            # handled fully by BacktestEngine during PnL calculations

        # Opening / increasing
        if new_qty != 0:
            self.avg_price = (
                (self.quantity * self.avg_price) + (fill_qty * fill_price)
            ) / new_qty

        self.quantity = new_qty


@dataclass
class Transaction:
    timestamp: float
    symbol: str
    quantity: float
    price: float


@dataclass
class Ledger:
    """Tracks real-time PnL, equity, positions, and transaction log.
    BacktestEngine updates this every bar.
    """

    cash: float = 1_000_000.0
    equity_curve: List[float] = field(default_factory=list)
    transactions: List[Transaction] = field(default_factory=list)
    positions: Dict[str, Position] = field(default_factory=dict)

    def record_transaction(
        self, bar: Bar, symbol: str, qty: float, price: float
    ) -> None:
        self.transactions.append(
            Transaction(
                timestamp=bar["timestamp"],
                symbol=symbol,
                quantity=qty,
                price=price,
            )
        )

    def update_position(self, symbol: str, qty: float, price: float) -> None:
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol=symbol)
        self.positions[symbol].update(price, qty)

    def mark_to_market(self, bar: Bar) -> None:
        """Update equity based on mark-to-market valuation."""
        total_value = self.cash
        for pos in self.positions.values():
            if pos.quantity != 0:
                total_value += pos.quantity * bar["close"]
        self.equity_curve.append(total_value)
