from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from ats.types import CapitalAllocPacket


@dataclass
class CapitalAllocatorConfig:
    """Config for RM3 capital allocation rules."""

    # Maximum gross leverage (sum of absolute symbol weights)
    max_gross_leverage: float = 2.0

    # Maximum weight per symbol (e.g. 0.25 => <=25% of capital in any one symbol)
    max_symbol_weight: float = 0.25


@dataclass
class CapitalAllocator:
    """RM3: translate capital packets into symbol weights / exposures.

    Input: a list of CapitalAllocPacket entries (symbol, capital, score, etc.)
    Output: a dict symbol -> weight, normalized and constrained by config.
    """

    config: CapitalAllocatorConfig = field(default_factory=CapitalAllocatorConfig)

    def allocate(self, packets: List[CapitalAllocPacket]) -> Dict[str, float]:
        """Turn CapitalAllocPacket list into normalized symbol weights.

        Returns a mapping symbol -> weight in [0, 1] whose sum is capped by
        max_gross_leverage and individual weights are capped by max_symbol_weight.
        """
        if not packets:
            return {}

        # 1) Aggregate capital per symbol
        symbol_capital: Dict[str, float] = {}
        for pkt in packets:
            sym = pkt["symbol"]
            cap = float(pkt["capital"])
            symbol_capital[sym] = symbol_capital.get(sym, 0.0) + cap

        total_capital = sum(symbol_capital.values())
        if total_capital <= 0.0:
            return {}

        # 2) Convert to preliminary weights
        weights: Dict[str, float] = {
            sym: cap / total_capital for sym, cap in symbol_capital.items()
        }

        # 3) Enforce per-symbol max cap
        max_w = self.config.max_symbol_weight
        if max_w > 0.0:
            for sym in list(weights.keys()):
                if weights[sym] > max_w:
                    weights[sym] = max_w

        # 4) Renormalize to respect max gross leverage
        gross = sum(weights.values())
        target_gross = (
            min(self.config.max_gross_leverage, gross) if gross > 0.0 else 0.0
        )
        if gross > 0.0 and target_gross != gross:
            scale = target_gross / gross
            for sym in list(weights.keys()):
                weights[sym] *= scale

        return weights
