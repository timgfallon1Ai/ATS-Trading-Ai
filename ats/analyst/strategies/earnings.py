from __future__ import annotations

from typing import Dict, List

import numpy as np


class EarningsStrategy:
    """Z-Ultra Earnings Model (F2 Depth)
    Detects post-earnings drift, gaps, guidance revisions,
    and regime-conditioned continuation probability.
    """

    def __init__(self):
        pass

    def _compute_features(self, history: Dict[str, Dict]) -> Dict[str, Dict]:
        features = {}

        for symbol, data in history.items():
            closes: List[float] = data["close"][-50:]
            volume: List[float] = data["volume"][-50:]
            gap = (closes[-1] - closes[-2]) / closes[-2]

            vol = np.std(closes[-20:])
            mom20 = (closes[-1] - closes[-20]) / closes[-20]
            mom5 = (closes[-1] - closes[-5]) / closes[-5]

            # F2 feature pack
            features[symbol] = {
                "gap": gap,
                "vol20": vol,
                "mom20": mom20,
                "mom5": mom5,
                "rel_volume": volume[-1] / (np.mean(volume[-20:]) + 1e-9),
                "shock_index": abs(gap) / (vol + 1e-9),
            }

        return features

    def _signal(self, f: Dict[str, float], regime: str) -> float:
        # Regime-adaptive continuation strength
        alpha = {
            "BULL": 1.0,
            "EXPANSION": 0.8,
            "NEUTRAL": 0.5,
            "VOLATILE": 0.3,
            "BEAR": -0.2,
            "CRISIS": -0.6,
        }[regime]

        # Post-earnings drift model
        base = f["gap"] * alpha
        continuation = f["mom5"] * 0.3 + f["mom20"] * 0.2

        return base + continuation

    def run(self, history: Dict[str, Dict], regime: str) -> Dict:
        features = self._compute_features(history)

        signal = {sym: self._signal(f, regime) for sym, f in features.items()}

        pnl_est = float(np.mean([s for s in signal.values()]))
        vol_est = float(np.std([s for s in signal.values()]))

        return {
            "features": features,
            "signal": signal,
            "pnl_estimate": pnl_est,
            "vol_estimate": vol_est,
        }
