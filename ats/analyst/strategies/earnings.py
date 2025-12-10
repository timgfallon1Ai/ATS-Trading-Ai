# ats/analyst/strategies/earnings.py
from __future__ import annotations

from typing import Dict, List, Mapping

from ..registry import register_strategy
from ..strategy_api import AnalystContext, StrategyBase, StrategySignal


@register_strategy
class EarningsStrategy(StrategyBase):
    """
    Earnings-driven strategy.

    Expects `context.metadata.get("earnings", {})` to be a mapping:
        {symbol: {"surprise": float, "direction": "beat" | "miss"}}

    If metadata is not present, this strategy remains silent.
    """

    def generate_signals(self, context: AnalystContext) -> List[StrategySignal]:
        signals: List[StrategySignal] = []

        earnings_meta: Mapping[str, Dict[str, object]] = context.metadata.get(
            "earnings", {}
        )
        if not earnings_meta:
            return signals

        base_size = float(self.config.get("base_size", 1.0))
        threshold = float(self.config.get("surprise_threshold", 0.02))

        for symbol, info in earnings_meta.items():
            surprise = float(info.get("surprise", 0.0))
            if abs(surprise) < threshold:
                continue

            direction = str(info.get("direction", "beat"))
            if direction == "beat":
                side = "long"
            elif direction == "miss":
                side = "short"
            else:
                side = "long" if surprise > 0 else "short"

            score = abs(surprise)
            size = base_size

            signals.append(
                StrategySignal(
                    symbol=symbol,
                    side=side,
                    size=size,
                    score=score,
                    confidence=min(1.0, score / threshold),
                    strategy=self.name,
                    timestamp=context.timestamp,
                    metadata=dict(info),
                )
            )

        return signals
