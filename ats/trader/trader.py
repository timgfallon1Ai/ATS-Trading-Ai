from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Iterable, List, TypedDict

from .execution_engine import ExecutionEngine
from .fill_types import Fill
from .market_data import MarketData
from .order_types import Order
from .portfolio import Portfolio
from .trade_ledger import TradeLedger


class TraderSnapshot(TypedDict):
    fills: List[Dict[str, object]]
    portfolio: Dict[str, object]
    trade_history: List[Dict[str, object]]


def _fill_to_dict(fill: Fill) -> Dict[str, object]:
    return {
        "symbol": fill.symbol,
        "side": fill.side,
        "size": fill.size,
        "price": fill.price,
        "timestamp": fill.timestamp.isoformat(),
        "notional": fill.notional,
    }


class Trader:
    """
    T1 - Thin trader.

    Responsibilities:
    - Hold MarketData snapshot
    - Hold Portfolio (cash + positions)
    - Use ExecutionEngine to convert Orders → Fills
    - Record fills in a TradeLedger
    - Return a serializable snapshot after each batch
    """

    def __init__(self, starting_capital: float = 100_000.0) -> None:
        self.market = MarketData()
        self.portfolio = Portfolio(starting_cash=starting_capital)
        self.execution = ExecutionEngine()
        self.ledger = TradeLedger()

    # ------------------------------------------------------------------ #
    # Market updates
    # ------------------------------------------------------------------ #

    def update_market(self, prices: Dict[str, float]) -> None:
        """Update the internal price snapshot."""
        self.market.update(prices)

    # ------------------------------------------------------------------ #
    # Order processing
    # ------------------------------------------------------------------ #

    def process_orders(
        self,
        orders: Iterable[Order],
        timestamp: datetime | None = None,
    ) -> TraderSnapshot:
        """
        Process a batch of orders and return a snapshot.

        Steps:
        - snapshot prices
        - execute orders
        - apply fills to portfolio
        - record fills in ledger
        - return snapshot (fills + portfolio + full history)
        """
        orders_list = list(orders)
        if not orders_list:
            prices = self.market.snapshot()
            return {
                "fills": [],
                "portfolio": self.portfolio.snapshot(prices),
                "trade_history": [_fill_to_dict(f) for f in self.ledger.history()],
            }

        prices = self.market.snapshot()
        ts = timestamp or datetime.now(timezone.utc)

        fills = self.execution.execute(orders_list, prices, ts)
        self.portfolio.apply_fills(fills)
        self.ledger.record(fills)

        snapshot: TraderSnapshot = {
            "fills": [_fill_to_dict(f) for f in fills],
            "portfolio": self.portfolio.snapshot(self.market.snapshot()),
            "trade_history": [_fill_to_dict(f) for f in self.ledger.history()],
        }
        return snapshot
