from __future__ import annotations

from typing import Dict

import numpy as np


class SwingStrategy:
    """Z-Ultra Swing Trading (F2)
    Captures 3–10 day oscillations using:
    - volatility-normalized wave patterns,
    - entropy gating,
    - regime-adaptive amplitude scoring.
    """

    def __init__(self):
        pass

    def _compute_features(self, history: Dict[str, Dict]) -> Dict[str, Dict]:
        features = {}

        for symbol, data in history.items():
            closes = np.array(data["close"][-80:])

            # 3-day and 10-day swings
            swing3 = closes[-1] - closes[-4]
            swing10 = closes[-1] - closes[-11]

            vol20 = np.std(closes[-20:])
            entropy10 = float(np.std(np.diff(closes[-10:])))

            features[symbol] = {
                "swing3": swing3 / (vol20 + 1e-9),
                "swing10": swing10 / (vol20 + 1e-9),
                "vol20": vol20,
                "entropy10": entropy10,
                "osc_strength": (swing3 + swing10) / (vol20 + 1e-9),
            }

        return features

    def _signal(self, f: Dict[str, float], regime: str) -> float:
        # Regime-scaled oscillation amplitude
        w = {
            "BULL": 0.8,
            "EXPANSION": 0.9,
            "NEUTRAL": 1.2,
            "VOLATILE": 1.5,
            "BEAR": 1.1,
            "CRISIS": 1.4,
        }[regime]

        entropy_gate = max(0.0, 1.0 - f["entropy10"])
        return f["osc_strength"] * w * entropy_gate

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
