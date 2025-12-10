# ats/analyst/strategies/pattern_recognition.py
from __future__ import annotations

from typing import Dict, List, Mapping

from ..registry import register_strategy
from ..strategy_api import AnalystContext, StrategyBase, StrategySignal


@register_strategy
class PatternRecognitionStrategy(StrategyBase):
    """
    Pattern-recognition strategy.

    Expects `context.metadata.get("pattern_signals", {})` to be a mapping:
        {symbol: {"side": "long" | "short", "score": float}}

    This is a hook for more advanced pattern engines (candlesticks, microstructure,
    ML pattern classifiers, etc.).
    """

    def generate_signals(self, context: AnalystContext) -> List[StrategySignal]:
        signals: List[StrategySignal] = []

        pattern_map: Mapping[str, Dict[str, object]] = context.metadata.get(
            "pattern_signals", {}
        )
        if not pattern_map:
            return signals

        threshold = float(self.config.get("score_threshold", 0.2))
        base_size = float(self.config.get("base_size", 1.0))

        for symbol, info in pattern_map.items():
            side = str(info.get("side", "flat"))
            score = float(info.get("score", 0.0))

            if side not in ("long", "short"):
                continue
            if abs(score) < threshold:
                continue

            signals.append(
                StrategySignal(
                    symbol=symbol,
                    side=side,
                    size=base_size,
                    score=abs(score),
                    confidence=min(1.0, abs(score)),
                    strategy=self.name,
                    timestamp=context.timestamp,
                    metadata=dict(info),
                )
            )

        return signals
