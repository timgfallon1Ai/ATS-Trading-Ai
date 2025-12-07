from __future__ import annotations

from typing import Any, Dict

from .latency_model import LatencyModel
from .slippage_model import SlippageModel


class LiveExecutionEngine:
    """Takes market orders → adds latency + slippage → returns fill price."""

    def __init__(self, latency: LatencyModel, slippage: SlippageModel):
        self.latency = latency
        self.slippage = slippage

    def execute(self, order: Dict[str, Any], quote: Dict[str, Any]) -> Dict[str, Any]:
        order = self.latency.apply(order)

        price = float(quote["close"])
        filled_price = self.slippage.apply(price)

        return {
            "symbol": order["symbol"],
            "size_delta": order["size_delta"],
            "price": filled_price,
        }
