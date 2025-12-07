from __future__ import annotations

from typing import Dict

import numpy as np


class MomentumStrategy:
    """Z-Ultra Momentum (F2 Depth)
    Multi-window momentum, volatility normalization,
    entropy gating, and regime-scaled trend conviction.
    """

    def __init__(self):
        pass

    def _compute_features(self, history: Dict[str, Dict]) -> Dict[str, Dict]:
        features = {}

        for symbol, data in history.items():
            closes = np.array(data["close"][-100:])
            vol20 = np.std(closes[-20:])
            mom20 = (closes[-1] - closes[-20]) / (closes[-20] + 1e-9)
            mom50 = (closes[-1] - closes[-50]) / (closes[-50] + 1e-9)

            entropy = float(np.std(np.diff(closes[-15:])))

            features[symbol] = {
                "mom20": mom20,
                "mom50": mom50,
                "vol20": vol20,
                "entropy": entropy,
                "trend_strength": (mom20 + mom50) / (vol20 + 1e-9),
            }

        return features

    def _signal(self, f: Dict[str, float], regime: str) -> float:
        # Conviction changes dramatically by regime
        w = {
            "BULL": 1.6,
            "EXPANSION": 1.2,
            "NEUTRAL": 0.8,
            "VOLATILE": 0.3,
            "BEAR": -0.5,
            "CRISIS": -1.0,
        }[regime]

        base = f["mom20"] * 0.6 + f["mom50"] * 0.4
        entropy_gate = max(0.0, 1.0 - f["entropy"])

        return base * w * entropy_gate

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
