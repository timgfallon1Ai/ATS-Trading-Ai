from __future__ import annotations

from typing import Dict

import numpy as np


class BreakoutStrategy:
    """Z-Ultra Breakout (F2 Depth)
    Detects volatility-normalized range expansions,
    compression → expansion transitions,
    and regime-scaled breakout conviction.
    """

    def __init__(self):
        pass

    def _compute_features(self, history: Dict[str, Dict]) -> Dict[str, Dict]:
        features = {}

        for symbol, data in history.items():
            highs = np.array(data["high"][-60:])
            lows = np.array(data["low"][-60:])
            closes = np.array(data["close"][-60:])

            range20 = (highs[-20:].max() - lows[-20:].min()) / (closes[-20] + 1e-9)
            vol20 = np.std(closes[-20:])
            compression = vol20 / (np.std(closes[-40:]) + 1e-9)

            # Breakout level = yesterday's high
            breakout_level = highs[-2]
            breakout_distance = (closes[-1] - breakout_level) / (vol20 + 1e-9)

            features[symbol] = {
                "range20": range20,
                "vol20": vol20,
                "compression": compression,
                "breakout_distance": breakout_distance,
                "momentum_factor": (closes[-1] - closes[-10]) / (closes[-10] + 1e-9),
            }

        return features

    def _signal(self, f: Dict[str, float], regime: str) -> float:
        # Conviction by regime
        w = {
            "BULL": 1.5,
            "EXPANSION": 1.2,
            "NEUTRAL": 0.9,
            "VOLATILE": 0.6,
            "BEAR": -0.3,
            "CRISIS": -0.8,
        }[regime]

        base = f["breakout_distance"]
        compression_boost = max(0.0, 1.0 - f["compression"])

        return (base + f["momentum_factor"] * 0.3) * w * (1 + compression_boost)

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
