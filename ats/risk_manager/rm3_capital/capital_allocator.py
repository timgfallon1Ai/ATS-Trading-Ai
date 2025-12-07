from __future__ import annotations

from typing import Any, Dict

from ats.types import AggregatedAllocation, CapitalAllocPacket

from .concentration_limits import ConcentrationLimits
from .exposure_rules import ExposureRules


class CapitalAllocator:
    """RM-3 Capital Allocation Engine.
    Converts RM-2 predictive risk + Aggregator signals into
    capital-scaled dollar allocations per symbol.

    Output: CapitalAllocPacket
    """

    def __init__(
        self,
        exposure: ExposureRules,
        concentration: ConcentrationLimits,
        base_capital: float = 1000.0,
    ):
        self.exposure = exposure
        self.concentration = concentration
        self.base_capital = base_capital

    # ---------------------------------------------------------
    # Compute raw dollar targets
    # ---------------------------------------------------------
    def _compute_raw_targets(
        self,
        aggs: Dict[str, AggregatedAllocation],
        predictive: Dict[str, Dict[str, Any]],
    ) -> Dict[str, float]:

        out: Dict[str, float] = {}

        for symbol, a in aggs.items():
            score = predictive.get(symbol, {}).get("model_score", 0.0)
            risk = predictive.get(symbol, {}).get("risk_score", 0.5)

            direction = 1 if score >= 0 else -1

            # Confidence-weighted target
            target = a["confidence"] * abs(score) * (1 - risk)

            out[symbol] = direction * target * self.base_capital

        return out

    # ---------------------------------------------------------
    # Main allocation pipeline
    # ---------------------------------------------------------
    def allocate(
        self,
        aggs: Dict[str, AggregatedAllocation],
        predictive: Dict[str, Dict[str, Any]],
        total_capital: float,
    ) -> Dict[str, CapitalAllocPacket]:

        # 1) Build raw targets
        raw = self._compute_raw_targets(aggs, predictive)

        # 2) Symbol exposure limits
        symbol_limited = {
            sym: self.exposure.apply_symbol_limit(val, total_capital)
            for sym, val in raw.items()
        }

        # 3) Gross exposure limit (portfolio-level)
        gross_limited = self.exposure.apply_gross_limit(symbol_limited, total_capital)

        # 4) Concentration limits (symbol)
        symbol_conc = self.concentration.apply_symbol_concentration(
            gross_limited, total_capital
        )

        # 5) Strategy concentration limits
        # Pull strategy_breakdown from aggs
        strategy_totals: Dict[str, float] = {}
        for sym, a in aggs.items():
            for strat, weight in a["strategy_breakdown"].items():
                strategy_totals[strat] = strategy_totals.get(
                    strat, 0
                ) + weight * symbol_conc.get(sym, 0)

        final_alloc = self.concentration.apply_strategy_concentration(
            symbol_conc, strategy_totals, total_capital
        )

        # 6) Build output packets
        out: Dict[str, CapitalAllocPacket] = {}

        for symbol, dollars in final_alloc.items():
            packet: CapitalAllocPacket = {
                "symbol": symbol,
                "target_dollars": float(dollars),
                "predicted_risk": predictive.get(symbol, {}).get(
                    "predicted_risk", 0.02
                ),
                "risk_score": predictive.get(symbol, {}).get("risk_score", 0.5),
                "regime": predictive.get(symbol, {}).get("regime", "neutral"),
            }
            out[symbol] = packet

        return out
