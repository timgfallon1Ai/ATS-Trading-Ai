# ats/backtester2/execution_simulator.py

from __future__ import annotations

from typing import Dict, List

from .order_builder import Order


class ExecutionFill:
    """Represents a completed fill event in the backtester."""

    def __init__(self, symbol: str, side: str, notional: float, price: float):
        self.symbol = symbol
        self.side = side  # BUY or SELL
        self.notional = notional
        self.price = price  # executed price (open price of next bar)

    def __repr__(self) -> str:
        return (
            f"ExecutionFill(symbol={self.symbol}, side={self.side}, "
            f"notional={self.notional:.2f}, price={self.price:.4f})"
        )


class ExecutionSimulator:
    """Simple deterministic execution simulator.
    Fills all orders at the NEXT BAR OPEN price.

    Inputs:
        - orders: List[Order] from OrderBuilder
        - open_prices: { symbol: open_price_of_next_bar }

    Output:
        - List[ExecutionFill]
    """

    def __init__(self):
        # Future extension: plug-in models for latency, slippage, microstructure.
        self.enable_slippage = False
        self.slippage_bps = 0.0  # basis points
        self.enable_latency = False

    def apply_slippage(self, price: float, side: str) -> float:
        """Applies optional slippage (disabled by default)."""
        if not self.enable_slippage:
            return price

        slip = price * (self.slippage_bps / 10_000)
        return price + slip if side == "BUY" else price - slip

    def fill_orders(
        self,
        orders: List[Order],
        open_prices: Dict[str, float],
    ) -> List[ExecutionFill]:
        fills: List[ExecutionFill] = []

        for order in orders:
            if order.symbol not in open_prices:
                # No valid data → cannot execute
                continue

            px = open_prices[order.symbol]

            # Apply latency hooks later if enabled
            # Apply slippage hook
            px_exec = self.apply_slippage(px, order.side)

            fills.append(
                ExecutionFill(
                    symbol=order.symbol,
                    side=order.side,
                    notional=order.notional,
                    price=px_exec,
                )
            )

        return fills
