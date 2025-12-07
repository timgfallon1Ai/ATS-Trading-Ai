from __future__ import annotations

from typing import Any, Dict, List

from ats.trader.execution_engine import ExecutionEngine
from ats.trader.fill_types import Fill
from ats.trader.market_data import MarketData
from ats.trader.order_types import Order
from ats.trader.portfolio import Portfolio
from ats.trader.trade_ledger import TradeLedger


class Trader:
    """
    T1 - Thin Institutional Trader.

    Responsibilities:
    - Hold the current market data snapshot.
    - Accept final risk-managed Orders.
    - Call the ExecutionEngine to obtain Fills.
    - Update the Portfolio and TradeLedger.
    - Return a JSON-friendly dict of fills + portfolio state.
    """

    def __init__(
        self,
        starting_capital: float = 1000.0,
        exec_engine: ExecutionEngine | None = None,
    ) -> None:
        self.market_data = MarketData()
        self.portfolio = Portfolio(starting_capital=starting_capital)
        self.exec_engine = exec_engine or ExecutionEngine()
        self.ledger = TradeLedger()

    # ------------------------------------------------------------------ #
    # Market data
    # ------------------------------------------------------------------ #
    def update_market(self, prices: Dict[str, float]) -> None:
        """Update internal market snapshot."""
        self.market_data.update(prices)

    # ------------------------------------------------------------------ #
    # Trading
    # ------------------------------------------------------------------ #
    def process_orders(self, orders: List[Order]) -> Dict[str, Any]:
        """
        Execute a batch of Orders against the current market snapshot.

        Returns:
            {
              "fills": [ {symbol, side, size, price, timestamp}, ... ],
              "portfolio": {...},
              "trade_history": [...],
            }
        """
        prices = self.market_data.snapshot

        fills = self.exec_engine.execute(orders, prices)
        for fill in fills:
            realized = self.portfolio.apply_fill(fill)
            if realized != 0.0:
                self.ledger.record(fill, realized)

        snapshot = self.portfolio.snapshot(prices)

        return {
            "fills": [self._fill_to_dict(f) for f in fills],
            "portfolio": snapshot,
            "trade_history": self.ledger.to_dicts(),
        }

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _fill_to_dict(fill: Fill) -> Dict[str, Any]:
        return {
            "symbol": fill.symbol,
            "side": fill.side,
            "size": fill.size,
            "price": fill.price,
            "timestamp": getattr(
                fill.timestamp, "isoformat", lambda: str(fill.timestamp)
            )(),
        }
