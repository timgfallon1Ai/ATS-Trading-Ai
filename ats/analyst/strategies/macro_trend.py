from __future__ import annotations

from typing import Dict

import numpy as np


class MacroTrendStrategy:
    """Z-Ultra Macro Trend Strategy (F2 Depth)

    Simulates macro alignment using long-window trend, volatility normalization,
    and cross-sectional macro drift estimation.

    Later will incorporate real macro streams:
        - VIX
        - DXY
        - US10Y
        - Sector ETFs
    """

    def __init__(self):
        pass

    def _compute_features(self, history: Dict[str, Dict]) -> Dict[str, Dict]:
        feats = {}

        for symbol, data in history.items():
            closes = np.array(data["close"][-200:])

            long_term = (closes[-1] - closes[-121]) / (closes[-121] + 1e-9)
            mid_term = (closes[-1] - closes[-61]) / (closes[-61] + 1e-9)
            short_term = (closes[-1] - closes[-21]) / (closes[-21] + 1e-9)

            vol60 = np.std(closes[-60:])
            vol120 = np.std(closes[-120:])

            trend_smooth = long_term * 0.5 + mid_term * 0.3 + short_term * 0.2

            feats[symbol] = {
                "trend_long": long_term,
                "trend_mid": mid_term,
                "trend_short": short_term,
                "trend_smooth": trend_smooth,
                "vol60": vol60,
                "vol120": vol120,
                "macro_strength": trend_smooth / (vol60 + 1e-9),
            }

        return feats

    def _signal(self, f: Dict[str, float], regime: str) -> float:
        # Macro trend is strongest in BULL and EXPANSION regimes
        w = {
            "BULL": 1.6,
            "EXPANSION": 1.3,
            "NEUTRAL": 1.0,
            "VOLATILE": 0.5,
            "BEAR": -0.5,
            "CRISIS": -0.9,
        }[regime]

        return f["macro_strength"] * w

    def run(self, history: Dict[str, Dict], regime: str) -> Dict:
        features = self._compute_features(history)
        signal = {s: self._signal(f, regime) for s, f in features.items()}

        pnl_est = float(np.mean(list(signal.values())))
        vol_est = float(np.std(list(signal.values())))

        return {
            "features": features,
            "signal": signal,
            "pnl_estimate": pnl_est,
            "vol_estimate": vol_est,
        }
