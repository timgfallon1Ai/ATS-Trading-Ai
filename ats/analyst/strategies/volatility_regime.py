from __future__ import annotations

import pandas as pd

from ats.analyst.strategy_api import FeatureRow, StrategySignal
from ats.analyst.strategy_base import StrategyBase


class VolatilityRegimeStrategy(StrategyBase):
    """Adjust risk appetite based on realised volatility."""

    low_vol: float = 0.10  # ~10% annualised
    high_vol: float = 0.40  # ~40% annualised

    def generate_signal(
        self,
        symbol: str,
        features: FeatureRow,
        history: pd.DataFrame,
    ) -> StrategySignal:
        vol = float(features.get("volatility", 0.0))

        if vol <= 0.0:
            return StrategySignal(symbol, self.name, 0.0, 0.0)

        if vol > self.high_vol:
            score = -0.6
            confidence = 0.7
        elif vol < self.low_vol:
            score = 0.3
            confidence = 0.4
        else:
            mid = 0.5 * (self.low_vol + self.high_vol)
            distance = abs(vol - mid) / (self.high_vol - self.low_vol)
            score = 0.4 if vol < mid else -0.4
            confidence = 0.5 * (1.0 - distance)

        return StrategySignal(
            symbol=symbol,
            strategy_name=self.name,
            score=score,
            confidence=confidence,
            metadata={"volatility": vol},
        )
