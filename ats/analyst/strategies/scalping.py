# ats/analyst/strategies/scalping.py
from __future__ import annotations

from typing import Dict, List, Mapping

from ..registry import register_strategy
from ..strategy_api import AnalystContext, StrategyBase, StrategySignal


@register_strategy
class ScalpingStrategy(StrategyBase):
    """
    Intraday scalping strategy placeholder.

    Expects high-frequency signals from an external microstructure engine via
    `context.metadata.get("scalping_signals", {})`:
        {symbol: {"side": "long" | "short", "score": float}}

    In the current daily-bar backtest, this will usually remain silent unless
    populated by live ingestion.
    """

    def generate_signals(self, context: AnalystContext) -> List[StrategySignal]:
        signals: List[StrategySignal] = []

        scalping_map: Mapping[str, Dict[str, object]] = context.metadata.get(
            "scalping_signals", {}
        )
        if not scalping_map:
            return signals

        threshold = float(self.config.get("score_threshold", 0.3))
        base_size = float(self.config.get("base_size", 0.5))

        for symbol, info in scalping_map.items():
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
