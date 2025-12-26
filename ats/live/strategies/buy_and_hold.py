from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Set

from ..broker import BrokerState
from ..types import OrderRequest, PriceTick


@dataclass
class BuyAndHoldStrategy:
    """Phase 15.1 baseline strategy.

    - For each symbol, buy once up to `notional_per_symbol` on the first time we see a tick.
    - Never sells (hold forever).
    """

    notional_per_symbol: float = 100.0
    allow_fractional: bool = False
    _bought: Set[str] = field(default_factory=set, init=False)

    def generate_orders(
        self, tick: PriceTick, state: BrokerState
    ) -> List[OrderRequest]:
        symbol = tick.symbol
        if symbol in self._bought:
            return []

        if tick.price <= 0:
            return []

        # If we already have a position, treat as bought.
        if abs(state.positions.get(symbol, 0.0)) > 1e-9:
            self._bought.add(symbol)
            return []

        # Conservative sizing: never exceed available cash in the state snapshot.
        budget = min(float(self.notional_per_symbol), float(state.cash))
        if budget <= 0:
            return []

        qty = budget / float(tick.price)
        if not self.allow_fractional:
            qty = float(int(qty))

        if qty <= 0:
            return []

        # Mark as bought optimistically; prevents repeat orders.
        self._bought.add(symbol)

        return [
            OrderRequest(
                symbol=symbol,
                side="buy",
                quantity=qty,
                tag="phase15.1_buy_and_hold",
            )
        ]
