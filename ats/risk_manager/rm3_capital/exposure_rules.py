from __future__ import annotations

from typing import Dict


class ExposureRules:
    """RM-3 Exposure Rules.
    Defines capital constraints at the symbol level and portfolio level.
    """

    def __init__(
        self,
        max_symbol_exposure: float = 0.15,  # 15% of capital
        max_gross_exposure: float = 1.0,  # 100% gross
    ):
        self.max_symbol_exposure = max_symbol_exposure
        self.max_gross_exposure = max_gross_exposure

    # ---------------------------------------------------------
    # Apply symbol-level exposure limits
    # ---------------------------------------------------------
    def apply_symbol_limit(self, dollars: float, total_capital: float) -> float:
        symbol_cap = total_capital * self.max_symbol_exposure
        return min(dollars, symbol_cap)

    # ---------------------------------------------------------
    # Apply portfolio-level exposure limits
    # ---------------------------------------------------------
    def apply_gross_limit(
        self, allocations: Dict[str, float], total_capital: float
    ) -> Dict[str, float]:
        gross = sum(abs(v) for v in allocations.values())
        limit = total_capital * self.max_gross_exposure

        if gross <= limit:
            return allocations

        # Scale down proportionally
        scale = limit / gross
        return {sym: qty * scale for sym, qty in allocations.items()}
