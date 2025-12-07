from __future__ import annotations

from typing import Dict

import numpy as np


class MeanReversionStrategy:
    """Z-Ultra Mean Reversion (F2)
    Uses volatility-scaled z-scores, spread compression,
    entropy inflection, and regime-weighted reversion probability.
    """

    def __init__(self):
        pass

    def _compute_features(self, history: Dict[str, Dict]) -> Dict[str, Dict]:
        features = {}

        for symbol, data in history.items():
            closes = np.array(data["close"][-60:])
            vol20 = np.std(closes[-20:])
            ma20 = np.mean(closes[-20:])
            z = (closes[-1] - ma20) / (vol20 + 1e-9)

            entropy = float(np.std(np.diff(closes[-10:])))

            features[symbol] = {
                "zscore": z,
                "vol20": vol20,
                "ma20": ma20,
                "entropy10": entropy,
                "stretch": abs(z) * entropy,
            }

        return features

    def _signal(self, f: Dict[str, float], regime: str) -> float:
        # Reversion probability by regime
        w = {
            "BULL": -0.3,  # reversion weaker in strong uptrends
            "EXPANSION": -0.2,
            "NEUTRAL": 1.0,
            "VOLATILE": 1.3,
            "BEAR": 1.4,
            "CRISIS": 2.0,  # extreme reversion strength
        }[regime]

        return -f["zscore"] * w  # inverse fade

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
