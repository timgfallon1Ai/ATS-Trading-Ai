# ats/analyst/strategies/__init__.py
from __future__ import annotations

"""
Strategy implementations for the ATS analyst layer.

Concrete strategies are defined in sibling modules and registered via the
`register_strategy` decorator from `ats.analyst.registry`.
"""

from .arbitrage import ArbitrageStrategy
from .breakout import BreakoutStrategy
from .earnings import EarningsStrategy
from .macro_trend import MacroTrendStrategy
from .mean_reversion import MeanReversionStrategy
from .momentum import MomentumStrategy
from .multi_factor import MultiFactorStrategy
from .news_sentiment import NewsSentimentStrategy
from .pattern_recognition import PatternRecognitionStrategy
from .scalping import ScalpingStrategy
from .swing import SwingStrategy
from .volatility_regime import VolatilityRegimeStrategy

__all__ = [
    "ArbitrageStrategy",
    "BreakoutStrategy",
    "EarningsStrategy",
    "MacroTrendStrategy",
    "MeanReversionStrategy",
    "MomentumStrategy",
    "MultiFactorStrategy",
    "NewsSentimentStrategy",
    "PatternRecognitionStrategy",
    "ScalpingStrategy",
    "SwingStrategy",
    "VolatilityRegimeStrategy",
]
