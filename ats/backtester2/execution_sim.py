# ats/backtester2/execution_sim.py

from __future__ import annotations

from typing import Any, Dict, List


class ExecutionSimulator:
    """Simulates fills at the next-bar-open."""

    def __init__(self, slippage_bps: float = 0.0):
        self.slippage_bps = slippage_bps

    def _apply_slippage(self, price: float) -> float:
        if self.slippage_bps == 0:
            return price
        return price * (1 + self.slippage_bps / 10000.0)

    def execute(
        self,
        sized_orders: List[Dict[str, Any]],
        slices: Dict[str, Any],
        timestamp: Any,
    ) -> List[Dict[str, Any]]:
        """sized_orders: [{symbol, qty, side}]
        returns fills: [{symbol, qty, price}]
        """
        fills = []

        for order in sized_orders:
            sym = order["symbol"]
            qty = float(order["qty"])
            if qty == 0:
                continue

            # Next-bar open price
            price = float(slices[sym]["open"])
            price = self._apply_slippage(price)

            fills.append(
                {
                    "timestamp": timestamp,
                    "symbol": sym,
                    "qty": qty,
                    "price": price,
                }
            )

        return fills
