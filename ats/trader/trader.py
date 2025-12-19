from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, TypedDict, Union

from .execution_engine import ExecutionEngine
from .fill_types import Fill
from .market_data import MarketData
from .order_types import Order
from .portfolio import Portfolio
from .trade_ledger import TradeLedger

TimestampLike = Union[datetime, int, float, str]


class TraderSnapshot(TypedDict):
    fills: List[Dict[str, Any]]
    portfolio: Dict[str, Any]
    trade_history: List[Dict[str, Any]]


def _coerce_timestamp(value: Optional[TimestampLike]) -> datetime:
    """
    Coerce various timestamp representations into a timezone-aware UTC datetime.

    Accepts:
      - datetime (naive treated as UTC)
      - int/float epoch seconds (also supports ms/us/ns via magnitude heuristics)
      - str ISO timestamps (supports trailing 'Z' for UTC)
      - str numeric epoch
    """
    if value is None:
        return datetime.now(timezone.utc)

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    if isinstance(value, (int, float)):
        v = float(value)

        # Heuristics: detect ms/us/ns epoch and normalize to seconds
        # seconds ~ 1e9, ms ~ 1e12, us ~ 1e15, ns ~ 1e18
        if v > 1e18:
            v = v / 1e9
        elif v > 1e15:
            v = v / 1e6
        elif v > 1e12:
            v = v / 1e3

        return datetime.fromtimestamp(v, tz=timezone.utc)

    if isinstance(value, str):
        s = value.strip()

        # Numeric epoch as string
        try:
            return _coerce_timestamp(float(s))
        except ValueError:
            pass

        # Support ISO "Z" suffix
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"

        # Try ISO parsing
        try:
            dt = datetime.fromisoformat(s)
        except ValueError:
            # Minimal fallbacks for common formats
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
                try:
                    dt = datetime.strptime(s, fmt)
                    break
                except ValueError:
                    dt = None  # type: ignore[assignment]
            if dt is None:
                # Last resort: "now" (prevents crashes; keeps system running)
                return datetime.now(timezone.utc)

        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    # Unknown type: don't crash the system; default to now.
    return datetime.now(timezone.utc)


def _fill_to_dict(fill: Fill) -> Dict[str, Any]:
    ts = _coerce_timestamp(getattr(fill, "timestamp", None))
    return {
        "symbol": fill.symbol,
        "side": fill.side,
        "size": float(fill.size),
        "price": float(fill.price),
        "timestamp": ts.isoformat(),
        "notional": float(fill.notional),
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

    def update_market(self, prices: Dict[str, float]) -> None:
        """Update the internal price snapshot."""
        self.market.update(prices)

    def process_orders(
        self,
        orders: Iterable[Order],
        timestamp: Optional[TimestampLike] = None,
    ) -> TraderSnapshot:
        """
        Process a batch of orders and return a snapshot.

        - Coerces timestamp into UTC datetime to remain compatible with
          backtester bar timestamps (float epochs / strings).
        """
        orders_list = list(orders)
        prices = self.market.snapshot()

        if not orders_list:
            return {
                "fills": [],
                "portfolio": self.portfolio.snapshot(prices),
                "trade_history": [_fill_to_dict(f) for f in self.ledger.history()],
            }

        ts = _coerce_timestamp(timestamp)

        fills = self.execution.execute(orders_list, prices, ts)
        self.portfolio.apply_fills(fills)
        self.ledger.record(fills)

        return {
            "fills": [_fill_to_dict(f) for f in fills],
            "portfolio": self.portfolio.snapshot(self.market.snapshot()),
            "trade_history": [_fill_to_dict(f) for f in self.ledger.history()],
        }
