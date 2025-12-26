from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List
from uuid import uuid4

from .broker import BrokerState
from .types import OrderFill, OrderRequest


@dataclass
class PaperBroker:
    """A simple in-memory paper broker.

    - Executes at the provided tick price (no slippage in Phase 15.1).
    - Enforces basic cash and position constraints.
    """

    starting_cash: float = 10_000.0
    name: str = "paper"

    _cash: float = field(init=False)
    _positions: Dict[str, float] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self._cash = float(self.starting_cash)

    def get_state(self) -> BrokerState:
        return BrokerState(cash=float(self._cash), positions=dict(self._positions))

    def place_order(
        self, order: OrderRequest, price: float, timestamp: datetime
    ) -> OrderFill:
        qty = float(order.quantity)
        if qty <= 0:
            raise ValueError(f"Order quantity must be > 0, got {qty}")

        px = float(price)
        if px <= 0:
            raise ValueError(f"Price must be > 0, got {px}")

        symbol = order.symbol
        side = order.side

        if side == "buy":
            cost = qty * px
            if cost > self._cash + 1e-9:
                raise ValueError(
                    f"Insufficient cash for buy: need {cost:.2f}, have {self._cash:.2f}"
                )
            self._cash -= cost
            self._positions[symbol] = self._positions.get(symbol, 0.0) + qty
        elif side == "sell":
            pos = self._positions.get(symbol, 0.0)
            if qty > pos + 1e-9:
                raise ValueError(
                    f"Insufficient position for sell: sell {qty}, have {pos}"
                )
            self._cash += qty * px
            new_pos = pos - qty
            if abs(new_pos) < 1e-9:
                self._positions.pop(symbol, None)
            else:
                self._positions[symbol] = new_pos
        else:
            raise ValueError(f"Unknown side: {side}")

        return OrderFill(
            order_id=str(uuid4()),
            symbol=symbol,
            side=side,
            quantity=qty,
            price=px,
            timestamp=timestamp,
            broker=self.name,
            raw={"tif": order.tif, "tag": order.tag, "order_type": order.order_type},
        )

    def flatten_all(
        self, prices: Dict[str, float], timestamp: datetime
    ) -> List[OrderFill]:
        fills: List[OrderFill] = []
        # Copy keys so we can mutate _positions while iterating
        for symbol, qty in list(self._positions.items()):
            px = float(prices.get(symbol, 0.0))
            if px <= 0:
                # If we don't have a price, skip flattening that symbol.
                continue

            side = "sell" if qty > 0 else "buy"
            fills.append(
                self.place_order(
                    OrderRequest(
                        symbol=symbol,
                        side=side,
                        quantity=abs(qty),
                        tag="kill_switch_flatten",
                    ),
                    price=px,
                    timestamp=timestamp,
                )
            )
        return fills

    def close(self) -> None:
        # Nothing to close for a pure in-memory broker.
        return
