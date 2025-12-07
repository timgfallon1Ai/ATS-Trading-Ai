from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
from ats.analyst.strategies.relative_strength import RelativeStrengthStrategy

from ats.analyst.strategies.arbitrage import ArbitrageStrategy
from ats.analyst.strategies.breakout import BreakoutStrategy
from ats.analyst.strategies.earnings import EarningsReactionStrategy
from ats.analyst.strategies.macro_trend import MacroTrendStrategy

# Import all 12 institutional strategies
from ats.analyst.strategies.mean_reversion import MeanReversionStrategy
from ats.analyst.strategies.momentum import MomentumStrategy
from ats.analyst.strategies.multi_factor import MultiFactorStrategy
from ats.analyst.strategies.news_sentiment import NewsSentimentStrategy
from ats.analyst.strategies.pattern_recognition import PatternRecognitionStrategy
from ats.analyst.strategies.scalping import ScalpingStrategy
from ats.analyst.strategies.volatility_regime import VolatilityRegimeStrategy


class HybridAnalystEngine:
    """Z-Ultra Hybrid Analyst Engine (H1-B + S2)

    Responsibilities:
        - orchestrates all 12 Z-Ultra strategies
        - merges:
            * features
            * signals
            * pnl & volatility estimates
        - produces a normalized master signal per symbol
        - emits strategy contribution weights for RM-3 capital allocator
    """

    def __init__(self):
        # Initialize all 12 models
        self.strategies = {
            "mean_reversion": MeanReversionStrategy(),
            "momentum": MomentumStrategy(),
            "vol_regime": VolatilityRegimeStrategy(),
            "breakout": BreakoutStrategy(),
            "multi_factor": MultiFactorStrategy(),
            "arbitrage": ArbitrageStrategy(),
            "earnings": EarningsReactionStrategy(),
            "relative_strength": RelativeStrengthStrategy(),
            "news_sentiment": NewsSentimentStrategy(),
            "pattern_recognition": PatternRecognitionStrategy(),
            "scalping": ScalpingStrategy(),
            "macro_trend": MacroTrendStrategy(),
        }

    # ----------------------------------------------------
    # Utility normalizers
    # ----------------------------------------------------

    def _normalize_signal(self, values: Dict[str, float]) -> Dict[str, float]:
        """Standard score normalization (z-score)."""
        arr = np.array(list(values.values()))
        mean = arr.mean()
        std = arr.std() + 1e-9
        return {s: (v - mean) / std for s, v in values.items()}

    def _blend_estimates(self, estimates: List[float]) -> float:
        """Aggregates PnL or volatility estimates across models."""
        return float(np.mean(estimates))

    # ----------------------------------------------------
    # MAIN EXECUTION
    # ----------------------------------------------------

    def run(
        self,
        history: Dict[str, Dict],
        regime: str,
    ) -> Dict[str, Any]:
        """Runs all strategies:
        1. Execute all 12 Z-Ultra models
        2. Normalize signals per strategy
        3. Merge into unified master signal
        4. Aggregate features
        5. Produce strategy breakdown for RM-3
        """
        strategy_outputs = {}
        all_signals = {}
        all_features = {}
        pnl_estimates = []
        vol_estimates = []

        # ----------------------------------------------------
        # Run each strategy
        # ----------------------------------------------------
        for name, strat in self.strategies.items():
            out = strat.run(history, regime)

            strategy_outputs[name] = out
            pnl_estimates.append(out["pnl_estimate"])
            vol_estimates.append(out["vol_estimate"])

        # ----------------------------------------------------
        # Collect per-strategy signals and normalize
        # ----------------------------------------------------
        normalized = {}
        for name, out in strategy_outputs.items():
            normalized[name] = self._normalize_signal(out["signal"])

        # ----------------------------------------------------
        # Aggregate final signal per symbol
        # Equal-weight S2 rule (institutional safe default)
        # ----------------------------------------------------
        symbols = list(history.keys())
        final_signal = dict.fromkeys(symbols, 0.0)

        for s in symbols:
            # average of all 12 normalized strategy signals
            final_signal[s] = float(
                np.mean([normalized[strat][s] for strat in self.strategies.keys()])
            )

        # ----------------------------------------------------
        # Merge features (per symbol deep union)
        # ----------------------------------------------------
        merged_features: Dict[str, Dict] = {s: {} for s in symbols}

        for name, out in strategy_outputs.items():
            feats = out["features"]
            for s in symbols:
                merged_features[s].update(feats.get(s, {}))

        # ----------------------------------------------------
        # Strategy contribution breakdown
        # Dict[strategy -> per-symbol contribution]
        # ----------------------------------------------------
        strat_breakdown = {
            name: {s: normalized[name][s] for s in symbols}
            for name in self.strategies.keys()
        }

        # ----------------------------------------------------
        # Final analyst output
        # ----------------------------------------------------
        return {
            "features": merged_features,
            "signal": final_signal,
            "pnl_estimate": self._blend_estimates(pnl_estimates),
            "vol_estimate": self._blend_estimates(vol_estimates),
            "strategy_breakdown": strat_breakdown,
        }
