from __future__ import annotations

from typing import Dict


class ConcentrationLimits:
    """Prevents over-concentration in:
    - individual symbols
    - strategy contributions
    """

    def __init__(
        self,
        max_symbol_weight: float = 0.20,  # 20% of portfolio
        max_strategy_weight: float = 0.35,  # 35% of portfolio
    ):
        self.max_symbol_weight = max_symbol_weight
        self.max_strategy_weight = max_strategy_weight

    # ---------------------------------------------------------
    # Symbol concentration — final pass
    # ---------------------------------------------------------
    def apply_symbol_concentration(
        self, alloc: Dict[str, float], total_capital: float
    ) -> Dict[str, float]:
        limit = total_capital * self.max_symbol_weight
        return {s: min(v, limit) for s, v in alloc.items()}

    # ---------------------------------------------------------
    # Strategy concentration
    # ---------------------------------------------------------
    def apply_strategy_concentration(
        self,
        alloc: Dict[str, float],
        strategy_breakdown: Dict[str, float],
        total_capital: float,
    ) -> Dict[str, float]:

        limit = total_capital * self.max_strategy_weight

        # Scale strategy blocks down if they exceed the limit
        scale = 1.0
        for strat, val in strategy_breakdown.items():
            if abs(val) > limit:
                scale = min(scale, limit / abs(val))

        if scale >= 1.0:
            return alloc

        return {s: v * scale for s, v in alloc.items()}
