from __future__ import annotations

from typing import List, Protocol

from .broker import BrokerState
from .types import OrderRequest, PriceTick


class Strategy(Protocol):
    """Strategy interface used by the LiveRunner."""

    def generate_orders(
        self, tick: PriceTick, state: BrokerState
    ) -> List[OrderRequest]: ...
