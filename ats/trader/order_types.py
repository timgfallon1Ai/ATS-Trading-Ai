from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Literal

Side = Literal["buy", "sell"]
OrderType = Literal["market"]


@dataclass
class Order:
    """
    Minimal order object consumed by the T1 trader.

    - symbol: ticker (e.g. "AAPL")
    - side: "buy" or "sell"
    - size: number of shares (must be positive)
    - order_type: currently only "market"
    - meta: free-form metadata (strategy id, tags, etc.)
    """

    symbol: str
    side: Side
    size: float
    order_type: OrderType = "market"
    meta: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.size <= 0:
            raise ValueError("Order.size must be positive")
        if self.side not in ("buy", "sell"):
            raise ValueError(f"Invalid side: {self.side!r}")
