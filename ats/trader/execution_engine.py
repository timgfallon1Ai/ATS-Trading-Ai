from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Union

from .fill_types import Fill
from .order_types import Order

TimestampLike = Union[datetime, int, float, str]


def _coerce_timestamp(value: Optional[TimestampLike]) -> datetime:
    """
    Coerce various timestamp representations into a timezone-aware UTC datetime.
    Mirrors trader.Trader coercion so ExecutionEngine is safe if called directly.
    """
    if value is None:
        return datetime.now(timezone.utc)

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    if isinstance(value, (int, float)):
        v = float(value)
        if v > 1e18:
            v = v / 1e9
        elif v > 1e15:
            v = v / 1e6
        elif v > 1e12:
            v = v / 1e3
        return datetime.fromtimestamp(v, tz=timezone.utc)

    if isinstance(value, str):
        s = value.strip()
        try:
            return _coerce_timestamp(float(s))
        except ValueError:
            pass
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            return datetime.now(timezone.utc)

    return datetime.now(timezone.utc)


class ExecutionEngine:
    """
    Deterministic, same-bar execution engine.

    For now:
    - fills entire order size
    - at the current snapshot price
    - no slippage or latency
    """

    def execute(
        self,
        orders: Iterable[Order],
        prices: Dict[str, float],
        timestamp: Optional[TimestampLike] = None,
    ) -> List[Fill]:
        ts = _coerce_timestamp(timestamp)
        fills: List[Fill] = []

        for order in orders:
            px = prices[order.symbol]
            fills.append(
                Fill(
                    symbol=order.symbol,
                    side=order.side,
                    size=order.size,
                    price=px,
                    timestamp=ts,
                )
            )

        return fills
