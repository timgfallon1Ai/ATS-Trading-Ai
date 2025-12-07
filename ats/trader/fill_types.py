from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Fill:
    """
    Execution result for a single order (or slice of an order).

    - symbol: ticker
    - side: "buy" or "sell"
    - size: executed quantity (shares)
    - price: execution price
    - timestamp: time of execution
    """

    symbol: str
    side: str
    size: float
    price: float
    timestamp: datetime
