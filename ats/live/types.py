from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Literal, Optional

Side = Literal["buy", "sell"]
OrderType = Literal["market"]


@dataclass(frozen=True)
class PriceTick:
    symbol: str
    price: float
    timestamp: datetime
    source: str = "unknown"


@dataclass(frozen=True)
class OrderRequest:
    symbol: str
    side: Side
    quantity: float
    order_type: OrderType = "market"
    tif: str = "DAY"
    tag: str = ""


@dataclass(frozen=True)
class OrderFill:
    order_id: str
    symbol: str
    side: Side
    quantity: float
    price: float
    timestamp: datetime
    broker: str = "unknown"
    raw: Optional[Dict[str, object]] = None
