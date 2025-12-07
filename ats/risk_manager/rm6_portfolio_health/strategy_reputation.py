from typing import Dict


class StrategyReputation:
    """Assigns reputation scores to strategies based on:
    - recent profitability
    - volatility
    - consistency
    """

    def __init__(self):
        self.scores: Dict[str, float] = {}

    def update(self, strategy_breakdown: Dict[str, float], pnl: float):
        for strat, weight in strategy_breakdown.items():
            current = self.scores.get(strat, 0.5)

            # Strategies that contributed positively gain reputation
            delta = pnl * weight * 0.1

            # Decay reputations slightly to maintain dynamism
            updated = (current * 0.95) + delta
            self.scores[strat] = max(0.0, min(1.0, updated))

    def get(self) -> Dict[str, float]:
        return self.scores.copy()
