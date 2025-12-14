from __future__ import annotations

import numpy as np
import pandas as pd

from ats.analyst.strategy_api import FeatureRow, StrategySignal
from ats.analyst.strategy_base import StrategyBase


class MultiFactorStrategy(StrategyBase):
    """Blend momentum, value, and volatility into a single score."""

    def generate_signal(
        self,
        symbol: str,
        features: FeatureRow,
        history: pd.DataFrame,
    ) -> StrategySignal:
        price = float(features.get("close", 0.0))
        sma_fast = float(features.get("sma_fast", 0.0))
        sma_slow = float(features.get("sma_slow", 0.0))
        vol = float(features.get("volatility", 0.0))

        if price <= 0.0 or sma_slow == 0.0:
            return StrategySignal(symbol, self.name, 0.0, 0.0)

        mom = (sma_fast - sma_slow) / sma_slow
        value = (sma_slow - price) / sma_slow

        target_vol = 0.25
        if vol <= 0.0:
            risk_adj = 0.0
        else:
            risk_adj = -abs(vol - target_vol) / target_vol

        raw_score = 0.5 * mom + 0.4 * value + 0.1 * risk_adj
        score = float(np.tanh(raw_score * 5.0))

        conf_components = [abs(mom), abs(value), max(0.0, -risk_adj)]
        confidence = min(1.0, sum(conf_components))

        return StrategySignal(
            symbol=symbol,
            strategy_name=self.name,
            score=score,
            confidence=confidence,
            metadata={"mom": mom, "value": value, "risk_adj": risk_adj},
        )
