from typing import Dict


class SlippageModel:
    """RM-5 Slippage Model

    Computes expected slippage using:
    - volatility
    - order size
    - entropy
    - base spread assumptions
    """

    def __init__(self, base_spread: float = 0.0005):
        self.base_spread = base_spread

    def compute_slippage(self, alloc: Dict, features: Dict) -> float:
        qty = alloc.get("qty", 0)
        vol = features.get("rv_15", 0.01)
        entropy = features.get("entropy", 0.5)

        # Slippage increases with:
        # - volatility
        # - entropy (market noise)
        # - quantity
        slip = self.base_spread + (vol * 0.3) + (entropy * 0.1) + (abs(qty) * 0.00001)

        return float(slip)
