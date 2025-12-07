from __future__ import annotations

from typing import Dict, List, Type

from ats.analyst.core.base import StrategyBase

# Import every strategy class
from ats.analyst.strategies.arbitrage import ArbitrageStrategy
from ats.analyst.strategies.breakout import BreakoutStrategy
from ats.analyst.strategies.earnings import EarningsStrategy
from ats.analyst.strategies.macro_trend import MacroTrendStrategy
from ats.analyst.strategies.mean_reversion import MeanReversionStrategy
from ats.analyst.strategies.momentum import MomentumStrategy
from ats.analyst.strategies.multi_factor import MultiFactorStrategy
from ats.analyst.strategies.news_sentiment import NewsSentimentStrategy
from ats.analyst.strategies.pattern_recognition import PatternRecognitionStrategy
from ats.analyst.strategies.scalping import ScalpingStrategy
from ats.analyst.strategies.swing import SwingStrategy
from ats.analyst.strategies.volatility_regime import VolatilityRegimeStrategy


class StrategyManager:
    """Central registry for all strategies.
    AnalystEngine owns one StrategyManager instance.
    """

    def __init__(self):
        self._registry: Dict[str, Type[StrategyBase]] = {
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
        }

    @property
    def all_names(self) -> List[str]:
        return list(self._registry.keys())

    def create(self, name: str, config=None) -> StrategyBase:
        if name not in self._registry:
            raise KeyError(f"Unknown strategy: {name}")

        cls = self._registry[name]
        return cls(config=config)
