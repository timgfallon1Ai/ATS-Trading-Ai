# ats/analyst/strategies/breakout.py
from __future__ import annotations

from typing import Dict, List

from ..registry import register_strategy
from ..strategy_api import AnalystContext, StrategyBase, StrategySignal


@register_strategy
class BreakoutStrategy(StrategyBase):
    """
    Simple trend-following breakout strategy.

    Goes long when price is meaningfully above the slow moving average with
    volatility confirming the move. Goes short for breakdowns.
    """

    def generate_signals(self, context: AnalystContext) -> List[StrategySignal]:
        signals: List[StrategySignal] = []

        breakout_threshold = float(self.config.get("breakout_threshold", 0.01))
        vol_floor = float(self.config.get("vol_floor", 0.0))

        for symbol in context.universe:
            feats: Dict[str, float] = context.features.get(symbol, {})
            close = float(feats.get("close", 0.0))
            ma_slow = float(feats.get("ma_slow", close or 1.0))
            vol20 = float(feats.get("volatility_20", 0.0))

            if ma_slow <= 0.0 or close <= 0.0:
                continue

            deviation = (close - ma_slow) / ma_slow
            if abs(deviation) < breakout_threshold:
                continue
            if vol20 < vol_floor:
                continue

            if deviation > 0.0:
                side = "long"
            else:
                side = "short"

            score = abs(deviation) * (1.0 + vol20)
            size = float(self.config.get("base_size", 1.0))

            signals.append(
                StrategySignal(
                    symbol=symbol,
                    side=side,
                    size=size,
                    score=score,
                    confidence=min(1.0, score),
                    strategy=self.name,
                    timestamp=context.timestamp,
                    metadata={
                        "close": close,
                        "ma_slow": ma_slow,
                        "volatility_20": vol20,
                        "deviation": deviation,
                    },
                )
            )

        return signals
