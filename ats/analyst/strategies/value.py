from __future__ import annotations

import numpy as np
import pandas as pd

from ats.analyst.strategy_api import FeatureRow, StrategySignal
from ats.analyst.strategy_base import StrategyBase


class ValueStrategy(StrategyBase):
    """Cheap-versus-expensive using the slow moving average as anchor."""

    def generate_signal(
        self,
        symbol: str,
        features: FeatureRow,
        history: pd.DataFrame,
    ) -> StrategySignal:
        price = float(features.get("close", 0.0))
        sma_slow = float(features.get("sma_slow", 0.0))

        if price <= 0.0 or sma_slow == 0.0:
            return StrategySignal(symbol, self.name, 0.0, 0.0)

        discount = (sma_slow - price) / sma_slow
        score = float(np.tanh(discount * 4.0))
        confidence = min(1.0, abs(discount) * 6.0)

        return StrategySignal(
            symbol=symbol,
            strategy_name=self.name,
            score=score,
            confidence=confidence,
            metadata={"discount": discount, "price": price, "anchor": sma_slow},
        )
