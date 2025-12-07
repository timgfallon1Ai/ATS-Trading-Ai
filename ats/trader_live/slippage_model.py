from __future__ import annotations

import random


class SlippageModel:
    """Applies a realistic slippage percentage."""

    def __init__(self, max_bps: float = 3.0):
        self.max_bps = max_bps

    def apply(self, price: float) -> float:
        slip = 1 + (random.random() * self.max_bps / 10000.0)
        return price * slip
