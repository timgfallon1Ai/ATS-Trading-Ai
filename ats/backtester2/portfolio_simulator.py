# ats/backtester2/portfolio_simulator.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .execution_simulator import ExecutionFill


@dataclass
class Position:
    symbol: str
    qty: float
    avg_price: float

    def update(self, fill: ExecutionFill):
        """Update position with a new fill.
        BUY: increases qty and adjusts avg_price
        SELL: decreases qty; if closing, realize PnL
        """
        if fill.side == "BUY":
            new_qty = self.qty + fill.notional / fill.price

            if self.qty == 0:
                # New long position
                self.avg_price = fill.price
            else:
                # Weighted average price update
                self.avg_price = (
                    (self.avg_price * self.qty)
                    + (fill.price * (fill.notional / fill.price))
                ) / new_qty

            self.qty = new_qty

        elif fill.side == "SELL":
            sell_qty = fill.notional / fill.price
            self.qty -= sell_qty

            # If position hits zero, reset avg price
            if abs(self.qty) < 1e-12:
                self.qty = 0.0
                self.avg_price = 0.0


class PortfolioSimulator:
    """Tracks all positions, cash, equity, and PnL across bar updates.
    Core constraints:
      - deterministic
      - fully multi-symbol
      - next-bar-open execution model

    Public API:
      - apply_fills(fills, open_prices)
      - mark_to_market(open_prices)
      - snapshot()
    """

    def __init__(self, initial_equity: float = 1_000.0):
        self.initial_equity = initial_equity
        self.cash = initial_equity
        self.positions: Dict[str, Position] = {}
        self.equity = initial_equity
        self.unrealized_pnl = 0.0
        self.realized_pnl = 0.0

    # ----------------------------------------------------
    # APPLY EXECUTIONS
    # ----------------------------------------------------
    def apply_fills(self, fills: List[ExecutionFill], open_prices: Dict[str, float]):
        """Update positions + cash based on executed fills."""
        for fill in fills:
            notional = fill.notional

            # BUY reduces cash; SELL increases cash
            if fill.side == "BUY":
                self.cash -= notional
            elif fill.side == "SELL":
                self.cash += notional

            # Update or create position
            pos = self.positions.get(fill.symbol)
            if pos is None:
                pos = Position(symbol=fill.symbol, qty=0.0, avg_price=0.0)
                self.positions[fill.symbol] = pos

            pos.update(fill)

        # After fills, update MTM
        self.mark_to_market(open_prices)

    # ----------------------------------------------------
    # MTM — MARK TO MARKET
    # ----------------------------------------------------
    def mark_to_market(self, open_prices: Dict[str, float]):
        """MTM: compute unrealized PnL and total equity."""
        self.unrealized_pnl = 0.0

        for sym, pos in self.positions.items():
            if pos.qty == 0:
                continue
            if sym not in open_prices:
                continue

            current_px = open_prices[sym]
            self.unrealized_pnl += (current_px - pos.avg_price) * pos.qty

        self.equity = self.cash + self.unrealized_pnl

    # ----------------------------------------------------
    # PORTFOLIO SNAPSHOT
    # ----------------------------------------------------
    def snapshot(self) -> Dict[str, float]:
        """Returns a stable portfolio state snapshot."""
        return {
            "cash": self.cash,
            "equity": self.equity,
            "unrealized_pnl": self.unrealized_pnl,
            "realized_pnl": self.realized_pnl,
            "positions": {
                sym: {"qty": pos.qty, "avg_price": pos.avg_price}
                for sym, pos in self.positions.items()
            },
        }
