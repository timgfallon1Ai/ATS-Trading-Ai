# ats/analyst/strategies/arbitrage.py
from __future__ import annotations

from typing import Dict, List

from ..registry import register_strategy
from ..strategy_api import AnalystContext, StrategyBase, StrategySignal


@register_strategy
class ArbitrageStrategy(StrategyBase):
    """
    Simple micro-arbitrage style strategy.

    Looks for large deviations between price and VWAP and bets on mean reversion.
    This is a placeholder for more sophisticated multi-leg or cross-venue arb.
    """

    def generate_signals(self, context: AnalystContext) -> List[StrategySignal]:
        signals: List[StrategySignal] = []

        threshold = float(self.config.get("threshold", 0.003))

        for symbol in context.universe:
            feats: Dict[str, float] = context.features.get(symbol, {})
            close = float(feats.get("close", 0.0))
            vwap = float(feats.get("vwap", close or 1.0))

            if vwap <= 0.0 or close <= 0.0:
                continue

            deviation = (close - vwap) / vwap

            if abs(deviation) < threshold:
                continue

            if deviation > 0.0:
                side = "short"
            else:
                side = "long"

            score = abs(deviation)
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
                        "vwap": vwap,
                        "deviation": deviation,
                    },
                )
            )

        return signals
