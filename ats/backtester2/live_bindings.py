from typing import Any, Dict

from ats.analyst.feature_engine import FeatureEngine
from ats.analyst.features import FeatureSchema
from ats.analyst.strategy_manager import StrategyManager


class LiveBindings:
    """Translates unified bars into analyst inputs,
    collects analyst outputs, and standardizes
    all formats for the aggregator.
    """

    def __init__(
        self, feature_engine: FeatureEngine, strategy_manager: StrategyManager
    ):
        self.feature_engine = feature_engine
        self.strategy_manager = strategy_manager

    def extract_features(self, bar: Dict[str, Any]) -> FeatureSchema:
        """Input: unified UBF bar for a single symbol or portfolio slice.
        Output: structured FeatureSchema.
        """
        return self.feature_engine.extract(bar)

    def generate_signals(self, features: FeatureSchema):
        """Apply all active strategies.

        Returns:
            list[StrategySignal]

        """
        return self.strategy_manager.generate(features)
