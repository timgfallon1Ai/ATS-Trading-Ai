from __future__ import annotations

import numpy as np
import pandas as pd

from ats.analyst.strategy_api import FeatureRow, StrategySignal
from ats.analyst.strategy_base import StrategyBase


class BreakoutStrategy(StrategyBase):
    """Detect simple 20-bar breakout patterns."""

    lookback: int = 20

    def generate_signal(
        self,
        symbol: str,
        features: FeatureRow,
        history: pd.DataFrame,
    ) -> StrategySignal:
        if history.shape[0] < self.lookback:
            return StrategySignal(symbol, self.name, 0.0, 0.0)

        closes = history["close"].astype(float)
        window = closes.iloc[-self.lookback :]
        current = float(window.iloc[-1])
        prior = window.iloc[:-1]

        high = float(prior.max())
        low = float(prior.min())
        if high == low:
            return StrategySignal(symbol, self.name, 0.0, 0.0)

        score = 0.0
        if current > high:
            overshoot = (current - high) / (high - low)
            score = float(np.tanh(overshoot * 5.0))
        elif current < low:
            undershoot = (low - current) / (high - low)
            score = float(-np.tanh(undershoot * 5.0))

        confidence = min(1.0, abs(score) * 1.5)

        return StrategySignal(
            symbol=symbol,
            strategy_name=self.name,
            score=score,
            confidence=confidence,
            metadata={"high": high, "low": low, "current": current},
        )
