# ats/backtester2/trade_router.py

from __future__ import annotations

from typing import Any, Dict, List


class TradeRouter:
    """Normalizes target-sized orders into the canonical execution instruction format.

    Input:
        [
            {"symbol": "AAPL", "target_qty": 15, "strength": 0.72, "reason": "..."},
            {"symbol": "TSLA", "target_qty": -10, "strength": -0.33},
        ]

    Output:
        [
            {"symbol": "AAPL", "target_qty": 15},
            {"symbol": "TSLA", "target_qty": -10},
        ]
    """

    def __init__(self):
        pass

    def route(self, sized_orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        final_orders = []

        for o in sized_orders:
            if o.get("target_qty", 0) == 0:
                continue

            final_orders.append(
                {
                    "symbol": o["symbol"],
                    "target_qty": int(o["target_qty"]),
                }
            )

        return final_orders
