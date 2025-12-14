from __future__ import annotations

import numpy as np
import pandas as pd

from ats.analyst.strategy_api import FeatureRow, StrategySignal
from ats.analyst.strategy_base import StrategyBase


class MacroTrendStrategy(StrategyBase):
    """Slow-moving trend based on long-horizon price change."""

    window: int = 100

    def generate_signal(
        self,
        symbol: str,
        features: FeatureRow,
        history: pd.DataFrame,
    ) -> StrategySignal:
        if history.shape[0] < self.window:
            return StrategySignal(symbol, self.name, 0.0, 0.0)

        closes = history["close"].astype(float)
        recent = closes.iloc[-1]
        past = closes.iloc[-self.window]

        if past <= 0.0:
            return StrategySignal(symbol, self.name, 0.0, 0.0)

        trend_ret = (recent / past) - 1.0
        score = float(np.tanh(trend_ret * 2.0))
        confidence = min(1.0, abs(trend_ret))

        return StrategySignal(
            symbol=symbol,
            strategy_name=self.name,
            score=score,
            confidence=confidence,
            metadata={"trend_return": trend_ret, "recent": recent, "past": past},
        )
