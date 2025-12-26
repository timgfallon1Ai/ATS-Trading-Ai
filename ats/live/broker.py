from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Optional, Sequence

from ats.trader.order import Order


class Broker(ABC):
    @abstractmethod
    def get_positions(self) -> Dict[str, float]:
        """Return positions as {symbol: quantity}. Positive=long, negative=short."""
        raise NotImplementedError

    @abstractmethod
    def place_order(self, order: Order, price: Optional[float] = None) -> None:
        """Place an order. For paper broker, price is used for fills/cash simulation."""
        raise NotImplementedError

    @abstractmethod
    def flatten(
        self,
        prices: Dict[str, float],
        symbols: Optional[Sequence[str]] = None,
    ) -> None:
        """Flatten positions for the given symbols (or all)."""
        raise NotImplementedError

    def close(self) -> None:
        """Optional cleanup hook."""
        return
