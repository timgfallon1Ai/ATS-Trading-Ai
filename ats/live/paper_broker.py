from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

from ats.live.broker import Broker
from ats.trader.order import Order

log = logging.getLogger("ats.live.paper_broker")


@dataclass
class PaperFill:
    symbol: str
    side: str
    qty: float
    price: float


class PaperBroker(Broker):
    """Very small paper broker for Phase 15.

    - Tracks positions in-memory
    - "Fills" at the provided price (usually the latest bar close)
    """

    def __init__(self, starting_cash: float = 100_000.0) -> None:
        self.cash: float = float(starting_cash)
        self._positions: Dict[str, float] = {}
        self.fills: List[PaperFill] = []
        self.orders: List[Order] = []

    def get_positions(self) -> Dict[str, float]:
        return dict(self._positions)

    def place_order(self, order: Order, price: Optional[float] = None) -> None:
        if price is None:
            raise ValueError("PaperBroker requires a price for fills")

        qty = float(order.size)
        if qty <= 0:
            return

        side = str(order.side).lower()
        sym = str(order.symbol).upper()

        self.orders.append(order)

        if side == "buy":
            self._positions[sym] = float(self._positions.get(sym, 0.0) + qty)
            self.cash -= qty * float(price)
        elif side == "sell":
            self._positions[sym] = float(self._positions.get(sym, 0.0) - qty)
            self.cash += qty * float(price)
        else:
            raise ValueError(f"Unknown side: {order.side}")

        self.fills.append(PaperFill(symbol=sym, side=side, qty=qty, price=float(price)))
        log.info(
            "PAPER FILL %s %s qty=%.6f @ %.4f", side.upper(), sym, qty, float(price)
        )

    def flatten(
        self,
        prices: Dict[str, float],
        symbols: Optional[Sequence[str]] = None,
    ) -> None:
        universe = (
            [s.upper() for s in symbols] if symbols else list(self._positions.keys())
        )
        for sym in universe:
            qty = float(self._positions.get(sym, 0.0))
            if abs(qty) < 1e-12:
                continue

            px = float(prices.get(sym, 0.0))
            if px <= 0:
                log.warning("No valid price to flatten %s; skipping", sym)
                continue

            if qty > 0:
                self.place_order(
                    Order(symbol=sym, side="sell", size=abs(qty), order_type="market"),
                    price=px,
                )
            else:
                self.place_order(
                    Order(symbol=sym, side="buy", size=abs(qty), order_type="market"),
                    price=px,
                )
