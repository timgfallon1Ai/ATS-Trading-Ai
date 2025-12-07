from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from ats.trader.fill_types import Fill
from ats.trader.order_types import Order


class ExecutionEngine:
    """
    Thin execution layer.

    In this version we:
    - Use either the order's explicit price or the latest market price.
    - Optionally apply a simple slippage model via `slippage_bps`.
    - Return fully-populated Fill objects.

    In later phases you can swap this for IBKR / broker adapters.
    """

    def __init__(self, slippage_bps: float = 0.0) -> None:
        self.slippage_bps = float(slippage_bps)

    def _apply_slippage(self, base_price: float, side: str) -> float:
        if self.slippage_bps == 0.0:
            return base_price

        delta = base_price * (self.slippage_bps / 10_000.0)
        side = side.lower()
        if side == "buy":
            return base_price + delta
        return base_price - delta

    def execute(
        self, orders: List[Order], market_prices: Dict[str, float]
    ) -> List[Fill]:
        """
        Convert Orders into Fills using current market prices.

        For now:
        - Any order without a price and no market price is skipped.
        - Slippage is applied deterministically by side.
        """
        fills: List[Fill] = []

        for order in orders:
            base_price = order.price
            if base_price is None:
                base_price = market_prices.get(order.symbol)

            if base_price is None:
                # In production you might log or raise; here we just skip
                continue

            exec_price = self._apply_slippage(float(base_price), order.side)
            ts = order.timestamp or datetime.utcnow()

            fills.append(
                Fill(
                    symbol=order.symbol,
                    side=order.side,
                    size=order.size,
                    price=exec_price,
                    timestamp=ts,
                )
            )

        return fills
