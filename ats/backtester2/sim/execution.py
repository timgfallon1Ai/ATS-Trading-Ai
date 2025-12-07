# ats/backtester2/sim/execution.py

from __future__ import annotations

from typing import List, Optional

from ats.backtester2.core.bar import Bar

from .fills import Fill
from .orders import Order


class ExecutionEngine:
    """Deterministic execution engine used in simulation.

    Features:
    - Market orders fill immediately at mid or bid/ask
    - Limit orders fill if bar touches limit price
    - Optional slippage model
    - Optional latency (in bars)
    """

    def __init__(
        self,
        use_bid_ask: bool = True,
        slippage_bps: float = 0.0,
        latency_bars: int = 0,
    ):
        self.use_bid_ask = use_bid_ask
        self.slippage_bps = slippage_bps
        self.latency_bars = latency_bars
        self._pending_orders: List[tuple[int, Order]] = []  # (remaining latency, order)

    # ------------------------------
    # Main entry point
    # ------------------------------
    def submit(self, order: Order) -> None:
        self._pending_orders.append((self.latency_bars, order))

    # ------------------------------
    # Called once per bar
    # ------------------------------
    def process(self, bar: Bar) -> List[Fill]:
        fills: List[Fill] = []
        still_pending: List[tuple[int, Order]] = []

        for remaining, order in self._pending_orders:
            if remaining > 0:
                still_pending.append((remaining - 1, order))
                continue

            fill = self._attempt_fill(order, bar)
            if fill:
                fills.append(fill)
            else:
                # Keep limit orders alive if not filled
                if order.order_type == "limit":
                    still_pending.append((0, order))

        self._pending_orders = still_pending
        return fills

    # ------------------------------
    # Fill logic
    # ------------------------------
    def _attempt_fill(self, order: Order, bar: Bar) -> Optional[Fill]:
        if order.order_type == "market":
            price = self._price_for_market(order, bar)
            return Fill(
                timestamp=bar["timestamp"],
                symbol=order.symbol,
                qty=order.qty,
                price=price,
            )

        if order.order_type == "limit":
            return self._attempt_limit_fill(order, bar)

        return None

    # ------------------------------
    # Market Orders
    # ------------------------------
    def _price_for_market(self, order: Order, bar: Bar) -> float:
        if self.use_bid_ask:
            price = bar["ask"] if order.is_buy else bar["bid"]
        else:
            price = bar["close"]

        return self._apply_slippage(price, order)

    # ------------------------------
    # Limit Orders
    # ------------------------------
    def _attempt_limit_fill(self, order: Order, bar: Bar) -> Optional[Fill]:
        if order.limit_price is None:
            return None

        touched = (order.is_buy and bar["low"] <= order.limit_price) or (
            order.is_sell and bar["high"] >= order.limit_price
        )

        if not touched:
            return None

        px = self._apply_slippage(order.limit_price, order)
        return Fill(
            timestamp=bar["timestamp"], symbol=order.symbol, qty=order.qty, price=px
        )

    # ------------------------------
    # Slippage
    # ------------------------------
    def _apply_slippage(self, price: float, order: Order) -> float:
        if self.slippage_bps <= 0:
            return price
        slip = price * (self.slippage_bps / 10_000)
        return price + slip if order.is_buy else price - slip
