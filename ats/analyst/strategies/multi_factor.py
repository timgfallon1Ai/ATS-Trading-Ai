# ats/analyst/strategies/multi_factor.py
from __future__ import annotations

from typing import Dict, List

from ..registry import register_strategy
from ..strategy_api import AnalystContext, StrategyBase, StrategySignal


@register_strategy
class MultiFactorStrategy(StrategyBase):
    """
    Composite multi-factor strategy.

    Combines simple factors:
    - momentum: fast vs slow MA
    - volatility: prefer moderate volatility regimes
    """

    def generate_signals(self, context: AnalystContext) -> List[StrategySignal]:
        signals: List[StrategySignal] = []

        mom_weight = float(self.config.get("momentum_weight", 1.0))
        vol_weight = float(self.config.get("vol_weight", 0.5))
        vol_target = float(self.config.get("vol_target", 0.02))
        score_threshold = float(self.config.get("score_threshold", 0.01))

        for symbol in context.universe:
            feats: Dict[str, float] = context.features.get(symbol, {})
            close = float(feats.get("close", 0.0))
            ma_fast = float(feats.get("ma_fast", close or 1.0))
            ma_slow = float(feats.get("ma_slow", close or 1.0))
            vol20 = float(feats.get("volatility_20", 0.0))

            if close <= 0.0 or ma_slow <= 0.0:
                continue

            momentum = (ma_fast - ma_slow) / ma_slow
            vol_norm = vol20 / max(close, 1e-9)

            vol_penalty = -abs(vol_norm - vol_target)

            composite = mom_weight * momentum + vol_weight * vol_penalty

            if composite > score_threshold:
                side = "long"
            elif composite < -score_threshold:
                side = "short"
            else:
                continue

            score = abs(composite)
            size = float(self.config.get("base_size", 1.0))

            signals.append(
                StrategySignal(
                    symbol=symbol,
                    side=side,
                    size=size,
                    score=score,
                    confidence=min(1.0, score / score_threshold),
                    strategy=self.name,
                    timestamp=context.timestamp,
                    metadata={
                        "close": close,
                        "ma_fast": ma_fast,
                        "ma_slow": ma_slow,
                        "volatility_20": vol20,
                        "momentum_factor": momentum,
                        "volatility_factor": vol_penalty,
                        "composite": composite,
                    },
                )
            )

        return signals
