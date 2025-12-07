# ats/backtester2/sim/orders.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

OrderSide = Literal["buy", "sell"]
OrderType = Literal["market", "limit"]


@dataclass
class Order:
    """Core order model used by the simulator and trader."""

    timestamp: float
    symbol: str
    side: OrderSide
    qty: float
    order_type: OrderType = "market"
    limit_price: float | None = None

    @property
    def is_buy(self) -> bool:
        return self.side == "buy"

    @property
    def is_sell(self) -> bool:
        return self.side == "sell"
