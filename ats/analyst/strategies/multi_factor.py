from __future__ import annotations

from typing import Dict

import numpy as np


class MultiFactorStrategy:
    """Z-Ultra Multi-Factor (F2 Depth)
    Institutional-grade factor model combining:
        - momentum factors
        - mean reversion factors
        - volatility & entropy factors
        - price/volume expansion factors
        - breakout probability
        - macro-regime alignment
    """

    def __init__(self):
        pass

    def _compute_features(self, history: Dict[str, Dict]) -> Dict[str, Dict]:
        features = {}

        for symbol, data in history.items():
            closes = np.array(data["close"][-120:])
            highs = np.array(data["high"][-120:])
            lows = np.array(data["low"][-120:])
            vols = np.array(data["volume"][-120:])

            # Factor components
            mom20 = (closes[-1] - closes[-21]) / (closes[-21] + 1e-9)
            mr10 = (closes[-6] - closes[-1]) / (np.std(closes[-10:]) + 1e-9)

            breakout_prob = (closes[-1] - highs[-20:].max()) / (
                np.std(closes[-20:]) + 1e-9
            )

            vol20 = np.std(closes[-20:])
            entropy20 = np.std(np.diff(closes[-20:]))
            volume_surge = vols[-1] / (np.mean(vols[-20:]) + 1e-9)

            features[symbol] = {
                "mom20": mom20,
                "mr10": mr10,
                "breakout_prob": breakout_prob,
                "vol20": vol20,
                "entropy20": entropy20,
                "volume_surge": volume_surge,
                "composite": (
                    mom20 * 0.4
                    + (-mr10) * 0.2
                    + breakout_prob * 0.3
                    + volume_surge * 0.1
                ),
            }

        return features

    def _signal(self, f: Dict[str, float], regime: str) -> float:
        # Regime scaling for factor conviction
        w = {
            "BULL": 1.4,
            "EXPANSION": 1.2,
            "NEUTRAL": 1.0,
            "VOLATILE": 0.8,
            "BEAR": -0.3,
            "CRISIS": -0.7,
        }[regime]

        entropy_penalty = max(0.2, 1.0 - f["entropy20"])
        return f["composite"] * w * entropy_penalty

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
