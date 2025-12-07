from __future__ import annotations

from typing import Dict

import numpy as np


class VolatilityRegimeStrategy:
    """Z-Ultra Volatility Regime Strategy (F2 Depth)

    Detects volatility expansions, compressions, entropy shifts, and
    regime-consistent volatility normalization. Acts as a meta-strategy
    that identifies when volatility favors trend, mean reversion,
    breakout, or defensive postures.
    """

    def __init__(self):
        pass

    def _compute_features(self, history: Dict[str, Dict]) -> Dict[str, Dict]:
        features = {}

        for symbol, data in history.items():
            closes = np.array(data["close"][-80:])
            highs = np.array(data["high"][-80:])
            lows = np.array(data["low"][-80:])

            vol20 = np.std(closes[-20:])
            vol60 = np.std(closes[-60:])
            vol_ratio = vol20 / (vol60 + 1e-9)

            entropy20 = np.std(np.diff(closes[-20:]))
            range_norm = (highs[-1] - lows[-1]) / (closes[-1] + 1e-9)

            features[symbol] = {
                "vol20": vol20,
                "vol60": vol60,
                "vol_ratio": vol_ratio,
                "entropy20": entropy20,
                "range_norm": range_norm,
                "vol_slope": (vol20 - np.std(closes[-30:]))
                / (np.std(closes[-30:]) + 1e-9),
            }

        return features

    def _signal(self, f: Dict[str, float], regime: str) -> float:
        # Regime weights for volatility alignment
        w = {
            "BULL": 0.6,
            "EXPANSION": 0.9,
            "NEUTRAL": 1.0,
            "VOLATILE": 1.6,
            "BEAR": 1.3,
            "CRISIS": 2.0,
        }[regime]

        # Volatility expansion that aligns with regime = strong signal
        core = f["vol_ratio"] * (1 + f["vol_slope"])
        entropy_penalty = max(0.1, 1.0 - f["entropy20"])

        return core * w * entropy_penalty

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
