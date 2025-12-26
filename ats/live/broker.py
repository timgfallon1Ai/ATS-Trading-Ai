from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Protocol

from .types import OrderFill, OrderRequest


@dataclass(frozen=True)
class BrokerState:
    cash: float
    positions: Dict[str, float]


class Broker(Protocol):
    """Minimal broker adapter interface for Phase 15.1."""

    name: str

    def get_state(self) -> BrokerState: ...

    def place_order(
        self, order: OrderRequest, price: float, timestamp: datetime
    ) -> OrderFill: ...

    def flatten_all(
        self, prices: Dict[str, float], timestamp: datetime
    ) -> List[OrderFill]: ...

    def close(self) -> None: ...
