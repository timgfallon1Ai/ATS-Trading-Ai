from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict

import numpy as np
import pandas as pd

from ats.analyst.strategy_api import FeatureRow


@dataclass
class FeatureEngine:
    """Lightweight feature calculator for daily bars."""

    sma_fast_window: int = 10
    sma_slow_window: int = 50
    rsi_window: int = 14
    vol_window: int = 20

    def compute(self, history: pd.DataFrame) -> FeatureRow:
        if history.empty:
            return {}

        if "close" not in history.columns:
            raise KeyError("history DataFrame must contain a 'close' column")

        close = history["close"].astype(float)
        features: Dict[str, float] = {}

        latest_close = float(close.iloc[-1])
        features["close"] = latest_close

        # 1d and 5d returns
        returns = close.pct_change()
        if len(returns) >= 2 and not np.all(np.isnan(returns.values)):
            last_ret = float(returns.iloc[-1])
        else:
            last_ret = 0.0
        features["return_1d"] = last_ret

        if len(returns) >= 5:
            window = returns.iloc[-5:]
            last_ret_5d = float(window.sum())
        else:
            last_ret_5d = float(np.nansum(returns.values))
        features["return_5d"] = last_ret_5d

        # Moving averages
        sma_fast = close.rolling(self.sma_fast_window).mean().iloc[-1]
        sma_slow = close.rolling(self.sma_slow_window).mean().iloc[-1]
        features["sma_fast"] = (
            float(sma_fast) if not math.isnan(sma_fast) else latest_close
        )
        features["sma_slow"] = (
            float(sma_slow) if not math.isnan(sma_slow) else latest_close
        )

        # RSI
        delta = close.diff()
        up = delta.clip(lower=0.0)
        down = -delta.clip(upper=0.0)

        roll_up = up.rolling(self.rsi_window).mean().iloc[-1]
        roll_down = down.rolling(self.rsi_window).mean().iloc[-1]

        if math.isnan(roll_up) or math.isnan(roll_down) or roll_down == 0:
            rsi = 50.0
        else:
            rs = roll_up / roll_down
            rsi = 100.0 - (100.0 / (1.0 + rs))

        features["rsi"] = float(rsi)

        # Realised volatility (annualised)
        valid_returns = returns.replace([np.inf, -np.inf], np.nan).dropna()
        if not valid_returns.empty:
            if len(valid_returns) >= self.vol_window:
                recent = valid_returns.iloc[-self.vol_window :]
            else:
                recent = valid_returns
            vol = float(recent.std() * math.sqrt(252.0))
        else:
            vol = 0.0

        features["volatility"] = vol

        # Volume (if available)
        if "volume" in history.columns:
            vol_col = history["volume"].astype(float)
            features["volume"] = float(vol_col.iloc[-1])

        return features
