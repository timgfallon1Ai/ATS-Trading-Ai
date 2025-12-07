import random
from typing import Dict


class FillsModel:
    """RM-5 Fill Probability Model

    Determines:
    - probability of fill
    - partial fill percentages
    - price adjustment based on slippage
    """

    def compute_fill(self, alloc: Dict, slippage: float, latency: float) -> Dict:
        qty = alloc.get("qty", 0)
        symbol = alloc["symbol"]

        # Fill probability drops with latency and slippage
        fill_prob = max(0.0, 1.0 - (slippage * 5) - (latency / 1000))

        # Determine if filled
        is_filled = random.random() < fill_prob

        # Partial fills
        if is_filled:
            partial = max(0.5, 1.0 - (slippage * 3))
            filled_qty = qty * partial
        else:
            filled_qty = 0.0

        return {
            "symbol": symbol,
            "requested_qty": qty,
            "filled_qty": float(filled_qty),
            "fill_probability": float(fill_prob),
            "slippage": float(slippage),
            "latency_ms": float(latency),
            "is_filled": is_filled,
        }
