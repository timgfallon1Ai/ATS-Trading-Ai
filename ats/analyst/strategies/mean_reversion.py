# ats/analyst/strategies/mean_reversion.py
from __future__ import annotations

from typing import Dict, List

from ..registry import register_strategy
from ..strategy_api import AnalystContext, StrategyBase, StrategySignal


@register_strategy
class MeanReversionStrategy(StrategyBase):
    """
    Mean-reversion strategy around the fast moving average.

    Buys dips below the fast MA and sells rallies above it.
    """

    def generate_signals(self, context: AnalystContext) -> List[StrategySignal]:
        signals: List[StrategySignal] = []

        band = float(self.config.get("band", 0.01))

        for symbol in context.universe:
            feats: Dict[str, float] = context.features.get(symbol, {})
            close = float(feats.get("close", 0.0))
            ma_fast = float(feats.get("ma_fast", close or 1.0))

            if close <= 0.0 or ma_fast <= 0.0:
                continue

            deviation = (close - ma_fast) / ma_fast

            if deviation > band:
                side = "short"
            elif deviation < -band:
                side = "long"
            else:
                continue

            score = abs(deviation)
            size = float(self.config.get("base_size", 1.0))

            signals.append(
                StrategySignal(
                    symbol=symbol,
                    side=side,
                    size=size,
                    score=score,
                    confidence=min(1.0, score / band),
                    strategy=self.name,
                    timestamp=context.timestamp,
                    metadata={
                        "close": close,
                        "ma_fast": ma_fast,
                        "deviation": deviation,
                    },
                )
            )

        return signals
