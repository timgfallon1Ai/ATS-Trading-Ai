from collections import defaultdict
from typing import Any, Dict, List


class AttributionEngine:
    """Breaks down PnL by:
    - strategy
    - symbol
    - factor (if supplied)
    """

    @staticmethod
    def by_symbol(trades: List[Dict[str, Any]]) -> Dict[str, float]:
        scores = defaultdict(float)
        for t in trades:
            scores[t["symbol"]] += t["pnl"]
        return dict(scores)

    @staticmethod
    def by_strategy(trades: List[Dict[str, Any]]) -> Dict[str, float]:
        # Optional: depends on strategy tagging in signal pipeline
        scores = defaultdict(float)
        for t in trades:
            if "strategy" in t:
                scores[t["strategy"]] += t["pnl"]
        return dict(scores)

    @staticmethod
    def by_factor(trades: List[Dict[str, Any]]) -> Dict[str, float]:
        # Optional: factor injection layer can be built later
        scores = defaultdict(float)
        for t in trades:
            if "factor" in t:
                scores[t["factor"]] += t["pnl"]
        return dict(scores)
