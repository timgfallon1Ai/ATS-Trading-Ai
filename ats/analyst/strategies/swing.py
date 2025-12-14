from __future__ import annotations

import numpy as np
import pandas as pd

from ats.analyst.strategy_api import FeatureRow, StrategySignal
from ats.analyst.strategy_base import StrategyBase


class SwingStrategy(StrategyBase):
    """Multi-day momentum on 5-day returns."""

    def generate_signal(
        self,
        symbol: str,
        features: FeatureRow,
        history: pd.DataFrame,
    ) -> StrategySignal:
        r5 = float(features.get("return_5d", 0.0))

        if r5 == 0.0:
            return StrategySignal(symbol, self.name, 0.0, 0.0)

        score = float(np.tanh(r5 * 3.0))
        confidence = min(1.0, abs(r5) * 5.0)

        return StrategySignal(
            symbol=symbol,
            strategy_name=self.name,
            score=score,
            confidence=confidence,
            metadata={"return_5d": r5},
        )
