from __future__ import annotations

import pandas as pd

from ats.analyst.strategy_api import FeatureRow, StrategySignal
from ats.analyst.strategy_base import StrategyBase


class ArbitrageStrategy(StrategyBase):
    """Placeholder for cross-asset / pairs arbitrage."""

    def generate_signal(
        self,
        symbol: str,
        features: FeatureRow,
        history: pd.DataFrame,
    ) -> StrategySignal:
        return StrategySignal(
            symbol=symbol,
            strategy_name=self.name,
            score=0.0,
            confidence=0.0,
            metadata={"reason": "arbitrage requires multiple instruments"},
        )
