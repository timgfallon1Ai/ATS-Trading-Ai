# ats/analyst/strategies/volatility_regime.py
from __future__ import annotations

from typing import Dict, List

from ats.analyst.registry import register_strategy
from ats.analyst.strategy_api import AnalystContext, StrategyBase, StrategySignal


@register_strategy
class VolatilityRegimeStrategy(StrategyBase):
    """
    Volatility-regime aware strategy.

    Uses volatility normalized by price to bias positioning:
    - Low volatility + uptrend → long.
    - High volatility + downtrend → short.
    """

    def generate_signals(self, context: AnalystContext) -> List[StrategySignal]:
        signals: List[StrategySignal] = []

        low_vol_threshold = float(self.config.get("low_vol_threshold", 0.01))
        high_vol_threshold = float(self.config.get("high_vol_threshold", 0.05))
        trend_threshold = float(self.config.get("trend_threshold", 0.005))

        for symbol in context.universe:
            feats: Dict[str, float] = context.features.get(symbol, {})
            close = float(feats.get("close", 0.0))
            ma_fast = float(feats.get("ma_fast", close or 1.0))
            ma_slow = float(feats.get("ma_slow", close or 1.0))
            vol20 = float(feats.get("volatility_20", 0.0))

            if close <= 0.0 or ma_slow <= 0.0:
                continue

            vol_norm = vol20 / max(close, 1e-9)
            trend = (ma_fast - ma_slow) / ma_slow

            if vol_norm < low_vol_threshold and trend > trend_threshold:
                side = "long"
                score = (low_vol_threshold - vol_norm) + abs(trend)
            elif vol_norm > high_vol_threshold and trend < -trend_threshold:
                side = "short"
                score = (vol_norm - high_vol_threshold) + abs(trend)
            else:
                continue

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
                        "ma_fast": ma_fast,
                        "ma_slow": ma_slow,
                        "volatility_20": vol20,
                        "vol_norm": vol_norm,
                        "trend": trend,
                    },
                )
            )

        return signals
