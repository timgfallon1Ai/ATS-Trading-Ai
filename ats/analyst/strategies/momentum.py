# ats/analyst/strategies/momentum.py
from __future__ import annotations

from typing import Dict, List

from ..registry import register_strategy
from ..strategy_api import AnalystContext, StrategyBase, StrategySignal


@register_strategy
class MomentumStrategy(StrategyBase):
    """
    Classic moving-average cross momentum strategy.

    Long when fast MA is above slow MA, short when fast MA is below slow MA.
    """

    def generate_signals(self, context: AnalystContext) -> List[StrategySignal]:
        signals: List[StrategySignal] = []

        threshold = float(self.config.get("cross_threshold", 0.001))

        for symbol in context.universe:
            feats: Dict[str, float] = context.features.get(symbol, {})
            close = float(feats.get("close", 0.0))
            ma_fast = float(feats.get("ma_fast", close or 1.0))
            ma_slow = float(feats.get("ma_slow", close or 1.0))

            if ma_fast <= 0.0 or ma_slow <= 0.0:
                continue

            ratio = ma_fast / ma_slow
            if ratio > 1.0 + threshold:
                side = "long"
                score = ratio - 1.0
            elif ratio < 1.0 - threshold:
                side = "short"
                score = (1.0 / ratio) - 1.0
            else:
                continue

            size = float(self.config.get("base_size", 1.0))

            signals.append(
                StrategySignal(
                    symbol=symbol,
                    side=side,
                    size=size,
                    score=score,
                    confidence=min(1.0, score / threshold),
                    strategy=self.name,
                    timestamp=context.timestamp,
                    metadata={
                        "close": close,
                        "ma_fast": ma_fast,
                        "ma_slow": ma_slow,
                        "ratio": ratio,
                    },
                )
            )

        return signals
