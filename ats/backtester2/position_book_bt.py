# ats/backtester2/position_book_bt.py

from __future__ import annotations

from typing import Any, Dict


class PositionBookBT:
    """Backtester-specific position tracker.

    Tracks for each symbol:
        - qty
        - avg_cost
        - realized_pnl
    """

    def __init__(self):
        self.positions: Dict[str, Dict[str, float]] = {}

    def apply_fill(self, fill: Dict[str, Any]):
        symbol = fill["symbol"]
        qty = float(fill["qty"])
        price = float(fill["price"])

        if symbol not in self.positions:
            self.positions[symbol] = {
                "qty": 0.0,
                "avg_cost": 0.0,
                "realized_pnl": 0.0,
            }

        pos = self.positions[symbol]
        old_qty = pos["qty"]
        old_cost = pos["avg_cost"]

        # BUY
        if qty > 0:
            new_qty = old_qty + qty
            if old_qty == 0:
                new_cost = price
            else:
                new_cost = (old_qty * old_cost + qty * price) / new_qty

            pos["qty"] = new_qty
            pos["avg_cost"] = new_cost

        # SELL
        else:
            sell_qty = abs(qty)
            sell_qty = min(sell_qty, old_qty)

            pnl = sell_qty * (price - old_cost)
            pos["realized_pnl"] += pnl

            pos["qty"] = old_qty - sell_qty

            # reset avg cost if flat
            if pos["qty"] == 0:
                pos["avg_cost"] = 0.0
