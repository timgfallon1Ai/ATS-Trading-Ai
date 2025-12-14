from __future__ import annotations

import numpy as np
import pandas as pd

from ats.analyst.strategy_api import FeatureRow, StrategySignal
from ats.analyst.strategy_base import StrategyBase


class MomentumStrategy(StrategyBase):
    """Classic moving-average momentum: fast MA vs slow MA."""

    def generate_signal(
        self,
        symbol: str,
        features: FeatureRow,
        history: pd.DataFrame,
    ) -> StrategySignal:
        price = float(features.get("close", 0.0))
        sma_fast = float(features.get("sma_fast", 0.0))
        sma_slow = float(features.get("sma_slow", 0.0))

        if price <= 0.0 or sma_fast == 0.0 or sma_slow == 0.0:
            return StrategySignal(symbol, self.name, 0.0, 0.0)

        spread = (sma_fast - sma_slow) / sma_slow
        score = float(np.tanh(spread * 5.0))
        confidence = min(1.0, abs(spread) * 10.0)

        return StrategySignal(
            symbol=symbol,
            strategy_name=self.name,
            score=score,
            confidence=confidence,
            metadata={"sma_fast": sma_fast, "sma_slow": sma_slow, "spread": spread},
        )
