from __future__ import annotations

import pandas as pd

from ats.analyst.strategy_api import FeatureRow, StrategySignal
from ats.analyst.strategy_base import StrategyBase


class PatternRecognitionStrategy(StrategyBase):
    """Very simple 3-bar candlestick pattern detector."""

    lookback: int = 3

    def generate_signal(
        self,
        symbol: str,
        features: FeatureRow,
        history: pd.DataFrame,
    ) -> StrategySignal:
        if history.shape[0] < self.lookback:
            return StrategySignal(symbol, self.name, 0.0, 0.0)

        window = history.iloc[-self.lookback :]

        if not {"open", "close"}.issubset(window.columns):
            return StrategySignal(symbol, self.name, 0.0, 0.0)

        closes = window["close"].astype(float)
        opens = window["open"].astype(float)
        up = closes > opens
        down = closes < opens

        score = 0.0
        confidence = 0.0

        if up.all():
            score = 0.7
            confidence = 0.6
        elif down.all():
            score = -0.7
            confidence = 0.6

        pattern_name = (
            "up_three" if score > 0 else "down_three" if score < 0 else "none"
        )

        return StrategySignal(
            symbol=symbol,
            strategy_name=self.name,
            score=score,
            confidence=confidence,
            metadata={"pattern": pattern_name},
        )
