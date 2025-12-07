# ats/backtester2/order_builder.py

from __future__ import annotations

from typing import Dict, List


class Order:
    """A simple atomic order object used by both:
        - backtester execution simulator
        - live trader execution pipeline

    All values are expressed in dollars (notional).
    """

    def __init__(self, symbol: str, side: str, notional: float):
        self.symbol = symbol
        self.side = side  # "BUY" or "SELL"
        self.notional = notional

    def __repr__(self) -> str:
        return f"Order(symbol={self.symbol}, side={self.side}, notional={self.notional:.2f})"


class OrderBuilder:
    """Converts:
        - target notionals (desired)
        - current positions  (actual)

    Into a list of atomic orders needed to transition the portfolio.

    Input:
        target_positions: { symbol: float }   (from PositionSizer)
        current_positions: { symbol: float }  (book-level notional)

    Output:
        List[Order]
    """

    def generate_orders(
        self, target_positions: Dict[str, float], current_positions: Dict[str, float]
    ) -> List[Order]:
        orders: List[Order] = []

        # Normalize missing symbols as zero
        all_symbols = set(target_positions.keys()) | set(current_positions.keys())

        for symbol in all_symbols:
            target = target_positions.get(symbol, 0.0)
            current = current_positions.get(symbol, 0.0)

            delta = target - current

            if abs(delta) < 1e-6:
                continue  # No action needed

            if delta > 0:
                # Need to BUY to increase exposure
                orders.append(Order(symbol, "BUY", abs(delta)))
            else:
                # Need to SELL to reduce exposure
                orders.append(Order(symbol, "SELL", abs(delta)))

        return orders
