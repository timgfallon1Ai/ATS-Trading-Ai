from __future__ import annotations

from typing import Dict, List

from ats.trader.fill_types import Fill
from ats.trader.order_types import Order


class ExecutionSimulator:
    """TT-A: same-bar execution model.
    Always fills at the *next bar open* or *current bar open* depending on config.
    """

    def __init__(self, same_bar: bool = True, slippage_bps: float = 1.0):
        self.same_bar = same_bar
        self.slippage = slippage_bps / 10000

    def execute(self, orders: List[Order], bar: Dict) -> List[Fill]:
        px = bar.get("open") or bar.get("close")
        px = float(px)

        slippage_px = px * self.slippage

        fills = []
        for order in orders:
            price = px + slippage_px if order.side == "buy" else px - slippage_px
            fills.append(
                Fill(
                    symbol=order.symbol,
                    side=order.side,
                    size=order.size,
                    price=price,
                    timestamp=order.timestamp,
                )
            )
        return fills
