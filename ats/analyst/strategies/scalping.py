from __future__ import annotations

from typing import Dict

import numpy as np


class ScalpingStrategy:
    """Z-Ultra Scalping (F2 Depth)
    Uses micro-momentum, volatility compression,
    and regime-scaled hit-rate modeling.
    """

    def __init__(self):
        pass

    def _compute_features(self, history: Dict[str, Dict]) -> Dict[str, Dict]:
        features = {}

        for symbol, data in history.items():
            closes = np.array(data["close"][-30:])
            highs = np.array(data["high"][-30:])
            lows = np.array(data["low"][-30:])

            vol10 = np.std(closes[-10:])
            spread = (highs[-1] - lows[-1]) / (closes[-1] + 1e-9)

            # micro momentum = last 3 bars
            mm = (closes[-1] - closes[-4]) / (vol10 + 1e-9)

            features[symbol] = {
                "vol10": vol10,
                "spread": spread,
                "micro_momentum": mm,
                "compression": vol10 / (np.std(closes[-20:]) + 1e-9),
            }

        return features

    def _signal(self, f: Dict[str, float], regime: str) -> float:
        # Scalping is extremely regime sensitive
        w = {
            "BULL": 1.0,
            "EXPANSION": 0.9,
            "NEUTRAL": 0.6,
            "VOLATILE": -0.2,  # avoid scalping in chop
            "BEAR": -0.5,
            "CRISIS": -1.0,
        }[regime]

        compression_gate = max(0.0, 1.0 - f["compression"])
        spread_penalty = max(0.0, 1.0 - f["spread"] * 5)

        return f["micro_momentum"] * w * compression_gate * spread_penalty

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
