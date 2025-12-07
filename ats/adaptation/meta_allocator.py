from typing import Dict


class MetaAllocator:
    """Converts reputation scores into strategy-level weight multipliers.

    reputation -1.0 → weight factor 0.1
    reputation  0.0 → weight factor 1.0
    reputation +1.0 → weight factor 3.0
    """

    def __init__(self):
        self.min_weight = 0.1
        self.max_weight = 3.0

    def compute_weights(self, reputation: Dict[str, float]) -> Dict[str, float]:
        weights = {}

        for strat, rep in reputation.items():
            # Normalize to multiplier range
            factor = 1 + rep * 2  # rep=-1 → -2, rep=1 → +2
            weights[strat] = max(self.min_weight, min(self.max_weight, factor))

        return weights
