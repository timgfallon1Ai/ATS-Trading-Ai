from collections import defaultdict
from typing import Dict


class ReputationEngine:
    """Tracks strategy-level performance and builds a 'reputation score':

    Inputs:
        - per-strategy attribution from RM orders
        - realized pnl from Trader
        - RM-7 governance warnings

    Output:
        - reputation scores between -1.0 and +1.0

    These scores are later used by the MetaAllocator.
    """

    def __init__(self):
        self.scores = defaultdict(float)
        self.decay = 0.995  # slow-decay rate per bar
        self.max_abs_score = 1.0

    def update(
        self,
        strategy_breakdown: Dict[str, float],
        pnl: float,
        governance_events: int = 0,
    ):
        # Apply decay first
        for s in self.scores.keys():
            self.scores[s] *= self.decay

        # Positive reinforcement (normalized by strategy contribution)
        for strat, weight in strategy_breakdown.items():
            reward = pnl * weight
            self.scores[strat] += reward

        # Penalize governance events
        for s in self.scores.keys():
            self.scores[s] -= governance_events * 0.01

        # Clamp to safe range
        for s, v in self.scores.items():
            self.scores[s] = max(-self.max_abs_score, min(self.max_abs_score, v))

    def get_scores(self):
        return dict(self.scores)
