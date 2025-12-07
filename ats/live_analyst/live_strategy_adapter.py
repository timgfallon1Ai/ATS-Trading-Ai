from __future__ import annotations

from typing import Any, Dict, List

from ats.analyst.strategies import (
    # The actual 12 strategies — already rebuilt in prior steps
    ArbitrageStrategy,
    BreakoutStrategy,
    EarningsStrategy,
    MacroTrendStrategy,
    MeanReversionStrategy,
    MomentumStrategy,
    MultiFactorStrategy,
    NewsSentimentStrategy,
    PatternRecognitionStrategy,
    ScalpingStrategy,
    SwingStrategy,
    VolatilityRegimeStrategy,
)

from .live_feature_schema import LiveFeatureSchema


class LiveStrategyAdapter:
    """Converts LiveFeatureSchema → 12 strategies → unified aggregated signals."""

    def __init__(self) -> None:
        self.strategies = [
            ArbitrageStrategy(),
            BreakoutStrategy(),
            EarningsStrategy(),
            MacroTrendStrategy(),
            MeanReversionStrategy(),
            MomentumStrategy(),
            MultiFactorStrategy(),
            NewsSentimentStrategy(),
            PatternRecognitionStrategy(),
            ScalpingStrategy(),
            SwingStrategy(),
            VolatilityRegimeStrategy(),
        ]

    def generate(self, feats: LiveFeatureSchema) -> List[Dict[str, Any]]:
        output: List[Dict[str, Any]] = []
        for strat in self.strategies:
            sig = strat.generate_signal(feats)
            if sig is not None:
                output.append(sig)
        return output
