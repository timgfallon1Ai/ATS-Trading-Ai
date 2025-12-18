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

    Input: a list of CapitalAllocPacket entries (symbol, target_dollars, score, etc.)
    Output: a dict symbol -> signed weight, normalized and constrained by config.

    Notes:
    - We preserve direction (long/short) based on target_dollars sign.
    - Normalization and caps are applied on gross exposure (abs weights).
    """

    config: CapitalAllocatorConfig = field(default_factory=CapitalAllocatorConfig)

    def allocate(self, packets: List[CapitalAllocPacket]) -> Dict[str, float]:
        """Turn CapitalAllocPacket list into normalized signed symbol weights."""
        if not packets:
            return {}

        # 1) Aggregate desired dollars per symbol
        symbol_capital: Dict[str, float] = {}
        for pkt in packets:
            sym = pkt.get("symbol")
            if not sym:
                continue

            # Canonical field is target_dollars; fall back to deprecated `capital`.
            raw = pkt.get("target_dollars")
            if raw is None:
                raw = pkt.get("capital", 0.0)

            cap = float(raw)
            if cap == 0.0:
                continue

            symbol_capital[sym] = symbol_capital.get(sym, 0.0) + cap

        if not symbol_capital:
            return {}

        # 2) Convert to preliminary signed weights (relative to gross capital)
        gross_capital = sum(abs(v) for v in symbol_capital.values())
        if gross_capital <= 0.0:
            return {}

        weights: Dict[str, float] = {
            sym: cap / gross_capital for sym, cap in symbol_capital.items()
        }

        # 3) Enforce per-symbol max cap on absolute weight
        max_w = float(self.config.max_symbol_weight)
        if max_w > 0.0:
            for sym in list(weights.keys()):
                if abs(weights[sym]) > max_w:
                    weights[sym] = max_w if weights[sym] > 0 else -max_w

        # 4) Renormalize to respect max gross leverage
        gross_w = sum(abs(w) for w in weights.values())
        target_gross = (
            min(float(self.config.max_gross_leverage), gross_w)
            if gross_w > 0.0
            else 0.0
        )
        if gross_w > 0.0 and target_gross != gross_w:
            scale = target_gross / gross_w
            for sym in list(weights.keys()):
                weights[sym] *= scale

        return weights
