from __future__ import annotations

import pandas as pd

from ats.analyst.strategy_api import FeatureRow, StrategySignal
from ats.analyst.strategy_base import StrategyBase


class EarningsStrategy(StrategyBase):
    """Placeholder for earnings-date specific logic."""

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
            metadata={"reason": "no earnings calendar wired into backtester"},
        )
