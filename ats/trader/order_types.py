from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Order:
    """
    Thin institutional order abstraction.

    - symbol: ticker, e.g. "AAPL"
    - side: "buy" or "sell"
    - size: number of shares (positive)
    - price: optional limit/reference price
    - timestamp: when the order was created
    """

    symbol: str
    side: str  # "buy" or "sell"
    size: float
    price: Optional[float] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self) -> None:
        self.side = self.side.lower()
        if self.side not in {"buy", "sell"}:
            raise ValueError("Order.side must be 'buy' or 'sell'")

        if self.size <= 0:
            raise ValueError("Order.size must be positive")

        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
