from __future__ import annotations

from typing import Dict, List, Sequence, Type

from ats.analyst.strategy_base import StrategyBase
from ats.analyst.strategies import (
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
    ValueStrategy,
)


STRATEGY_REGISTRY: Dict[str, Type[StrategyBase]] = {
    "arbitrage": ArbitrageStrategy,
    "breakout": BreakoutStrategy,
    "earnings": EarningsStrategy,
    "macro_trend": MacroTrendStrategy,
    "mean_reversion": MeanReversionStrategy,
    "momentum": MomentumStrategy,
    "multi_factor": MultiFactorStrategy,
    "news_sentiment": NewsSentimentStrategy,
    "pattern_recognition": PatternRecognitionStrategy,
    "scalping": ScalpingStrategy,
    "swing": SwingStrategy,
    "volatility_regime": VolatilityRegimeStrategy,
    "value": ValueStrategy,
}


def available_strategies() -> List[str]:
    return sorted(STRATEGY_REGISTRY.keys())


def make_strategies(names: Sequence[str] = None) -> List[StrategyBase]:
    if names is None:
        names = available_strategies()
    result: List[StrategyBase] = []
    for name in names:
        cls = STRATEGY_REGISTRY.get(name)
        if cls is None:
            raise KeyError(f"Unknown strategy name: {name}")
        result.append(cls())
    return result
