# ats/backtester2/portfolio_sim.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class PortfolioState:
    equity: float = 0.0
    cash: float = 0.0
    timestamp: Any = None


class PortfolioSimulator:
    """Tracks equity, cash, and equity curve for the entire backtest."""

    def __init__(self, initial_equity: float):
        self.state = PortfolioState(
            equity=initial_equity,
            cash=initial_equity,
        )
        self.equity_curve: List[Dict[str, Any]] = []

    def mark_to_market(
        self,
        positions: Dict[str, Dict[str, float]],
        slices: Dict[str, Any],
        timestamp: Any,
    ):
        """Revalue all positions at the current timestamp using OHLCV slices."""
        total_value = 0.0

        for sym, pos in positions.items():
            qty = pos.get("qty", 0.0)
            if qty == 0:
                continue

            # Use close price for valuation
            price = float(slices[sym]["close"])
            total_value += qty * price

        equity = self.state.cash + total_value

        self.state.equity = equity
        self.state.timestamp = timestamp

        self.equity_curve.append(
            {
                "timestamp": timestamp,
                "equity": equity,
                "cash": self.state.cash,
                "positions_value": total_value,
            }
        )

    def apply_cash_change(self, amount: float):
        self.state.cash += amount
