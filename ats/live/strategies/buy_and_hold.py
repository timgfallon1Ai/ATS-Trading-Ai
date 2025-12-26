from __future__ import annotations

import logging
from typing import Dict, List, Set

from ats.live.broker import Broker
from ats.live.strategy import LiveStrategy
from ats.live.types import Bar
from ats.trader.order import Order

log = logging.getLogger("ats.live.strategies.buy_and_hold")


class BuyAndHoldStrategy(LiveStrategy):
    name = "buy_and_hold"

    def __init__(self, notional_per_symbol: float, allow_fractional: bool) -> None:
        self.notional_per_symbol = float(notional_per_symbol)
        self.allow_fractional = bool(allow_fractional)
        self._bought: Set[str] = set()

    def on_tick(self, bars: Dict[str, Bar], broker: Broker) -> List[Order]:
        orders: List[Order] = []

        for sym, bar in bars.items():
            sym = sym.upper()
            if sym in self._bought:
                continue

            px = float(bar.close)
            if px <= 0:
                continue

            qty = self.notional_per_symbol / px
            if not self.allow_fractional:
                qty = float(int(qty))

            if qty <= 0:
                log.info(
                    "Skipping %s (notional %.2f too small vs price %.2f)",
                    sym,
                    self.notional_per_symbol,
                    px,
                )
                self._bought.add(sym)
                continue

            orders.append(Order(symbol=sym, side="buy", size=qty, order_type="market"))
            self._bought.add(sym)

        return orders
