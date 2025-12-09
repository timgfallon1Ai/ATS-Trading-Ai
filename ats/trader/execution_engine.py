from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Iterable, List

from .fill_types import Fill
from .order_types import Order


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
        timestamp: datetime | None = None,
    ) -> List[Fill]:
        ts = timestamp or datetime.now(timezone.utc)
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
