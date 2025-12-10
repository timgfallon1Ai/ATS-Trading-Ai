# ats/analyst/strategies/macro_trend.py
from __future__ import annotations

from typing import Dict, List

from ..registry import register_strategy
from ..strategy_api import AnalystContext, StrategyBase, StrategySignal


@register_strategy
class MacroTrendStrategy(StrategyBase):
    """
    Slow-moving macro trend strategy.

    Uses slow moving average and volatility to bias towards:
    - long in stable uptrends
    - short in stressed downtrends
    """

    def generate_signals(self, context: AnalystContext) -> List[StrategySignal]:
        signals: List[StrategySignal] = []

        up_threshold = float(self.config.get("up_threshold", 0.01))
        down_threshold = float(self.config.get("down_threshold", -0.01))

        for symbol in context.universe:
            feats: Dict[str, float] = context.features.get(symbol, {})
            close = float(feats.get("close", 0.0))
            ma_slow = float(feats.get("ma_slow", close or 1.0))
            vol20 = float(feats.get("volatility_20", 0.0))

            if close <= 0.0 or ma_slow <= 0.0:
                continue

            trend = (close - ma_slow) / ma_slow

            if trend > up_threshold and vol20 >= 0.0:
                side = "long"
            elif trend < down_threshold and vol20 >= 0.0:
                side = "short"
            else:
                continue

            score = abs(trend)
            size = float(self.config.get("base_size", 1.0))

            signals.append(
                StrategySignal(
                    symbol=symbol,
                    side=side,
                    size=size,
                    score=score,
                    confidence=min(1.0, score / up_threshold),
                    strategy=self.name,
                    timestamp=context.timestamp,
                    metadata={
                        "close": close,
                        "ma_slow": ma_slow,
                        "volatility_20": vol20,
                        "trend": trend,
                    },
                )
            )

        return signals
