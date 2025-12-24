from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Iterable, List, TypedDict, Union

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


def _coerce_timestamp(ts: Union[datetime, str, None]) -> datetime:
    if ts is None:
        return datetime.now(timezone.utc)

    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)

    if isinstance(ts, str):
        s = ts.strip()
        try:
            # ISO strings sometimes end with Z
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            return datetime.now(timezone.utc)

    return datetime.now(timezone.utc)


def _fill_to_dict(fill: Fill) -> Dict[str, object]:
    ts = (
        fill.timestamp.isoformat()
        if hasattr(fill.timestamp, "isoformat")
        else str(fill.timestamp)
    )
    return {
        "symbol": fill.symbol,
        "side": fill.side,
        "size": fill.size,
        "price": fill.price,
        "timestamp": ts,
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

    Phase9.3:
    - Adds `flatten_positions()` for kill-switch / emergency stop behavior
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
        self.market.update(prices)

    # ------------------------------------------------------------------ #
    # Order processing
    # ------------------------------------------------------------------ #

    def process_orders(
        self,
        orders: Iterable[Order],
        timestamp: Union[datetime, str, None] = None,
    ) -> TraderSnapshot:
        orders_list = list(orders)
        prices = self.market.snapshot()
        ts = _coerce_timestamp(timestamp)

        if not orders_list:
            return {
                "fills": [],
                "portfolio": self.portfolio.snapshot(prices),
                "trade_history": [_fill_to_dict(f) for f in self.ledger.history()],
            }

        fills = self.execution.execute(orders_list, prices, ts)
        self.portfolio.apply_fills(fills)
        self.ledger.record(fills)

        return {
            "fills": [_fill_to_dict(f) for f in fills],
            "portfolio": self.portfolio.snapshot(self.market.snapshot()),
            "trade_history": [_fill_to_dict(f) for f in self.ledger.history()],
        }

    # ------------------------------------------------------------------ #
    # Emergency flatten
    # ------------------------------------------------------------------ #

    def flatten_positions(
        self,
        timestamp: Union[datetime, str, None] = None,
        *,
        meta_reason: str = "flatten",
    ) -> TraderSnapshot:
        """
        Flatten all open positions with market orders (risk-reducing action).
        Does NOT run through RiskManager; intended for emergency stop / kill-switch.
        """
        orders: List[Order] = []
        for sym, pos in self.portfolio.positions.items():
            qty = float(getattr(pos, "quantity", 0.0))
            if abs(qty) < 1e-12:
                continue
            side = "sell" if qty > 0 else "buy"
            orders.append(
                Order(
                    symbol=str(sym),
                    side=side,  # type: ignore[arg-type]
                    size=abs(qty),
                    order_type="market",
                    meta={"reason": meta_reason},
                )
            )

        return self.process_orders(orders, timestamp=timestamp)
