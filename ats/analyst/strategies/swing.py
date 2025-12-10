# ats/analyst/strategies/swing.py
from __future__ import annotations

from typing import Dict, List

from ..registry import register_strategy
from ..strategy_api import AnalystContext, StrategyBase, StrategySignal


@register_strategy
class SwingStrategy(StrategyBase):
    """
    Swing-trading strategy.

    Looks for pullbacks within a broader trend:
    - Uptrend: slow MA above price history; buy dips below fast MA.
    - Downtrend: slow MA below; sell rallies above fast MA.
    """

    def generate_signals(self, context: AnalystContext) -> List[StrategySignal]:
        signals: List[StrategySignal] = []

        pullback = float(self.config.get("pullback", 0.01))
        trend_threshold = float(self.config.get("trend_threshold", 0.005))

        for symbol in context.universe:
            feats: Dict[str, float] = context.features.get(symbol, {})
            close = float(feats.get("close", 0.0))
            ma_fast = float(feats.get("ma_fast", close or 1.0))
            ma_slow = float(feats.get("ma_slow", close or 1.0))

            if close <= 0.0 or ma_slow <= 0.0:
                continue

            trend = (ma_fast - ma_slow) / ma_slow

            if trend > trend_threshold and close < ma_fast * (1.0 - pullback):
                side = "long"
            elif trend < -trend_threshold and close > ma_fast * (1.0 + pullback):
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
                    confidence=min(1.0, score / trend_threshold),
                    strategy=self.name,
                    timestamp=context.timestamp,
                    metadata={
                        "close": close,
                        "ma_fast": ma_fast,
                        "ma_slow": ma_slow,
                        "trend": trend,
                    },
                )
            )

        return signals
