from __future__ import annotations

from typing import Dict

import numpy as np


class ArbitrageStrategy:
    """Z-Ultra Cross-Sectional Arbitrage (F2 Depth)

    Identifies temporary mispricings between:
        - symbol vs sector basket
        - symbol vs index-relative beta
        - volatility-normalized deviations
        - regime-adjusted mean expectations
    """

    def __init__(self):
        pass

    def _compute_features(self, history: Dict[str, Dict]) -> Dict[str, Dict]:
        features = {}

        # Build index proxy (simple mean of all closes)
        all_closes = [np.array(v["close"][-60:]) for v in history.values()]
        index_proxy = np.mean(all_closes, axis=0)

        for symbol, data in history.items():
            closes = np.array(data["close"][-60:])
            vol20 = np.std(closes[-20:])
            vol60 = np.std(closes[-60:])

            # Beta estimate
            beta = np.cov(closes[-40:], index_proxy[-40:])[0][1] / (
                np.var(index_proxy[-40:]) + 1e-9
            )

            expected = beta * index_proxy[-1]
            deviation = (closes[-1] - expected) / (vol20 + 1e-9)

            features[symbol] = {
                "vol20": vol20,
                "vol60": vol60,
                "beta": beta,
                "expected_price": expected,
                "deviation": deviation,
                "arb_strength": deviation / (vol20 + 1e-9),
            }

        return features

    def _signal(self, f: Dict[str, float], regime: str) -> float:
        # Arbitrage is strongest in neutral or mean-reverting regimes
        w = {
            "BULL": 0.5,
            "EXPANSION": 0.7,
            "NEUTRAL": 1.4,
            "VOLATILE": 1.1,
            "BEAR": 0.8,
            "CRISIS": 0.4,
        }[regime]

        return -f["arb_strength"] * w  # negative deviation → long, positive → short

    def run(self, history: Dict[str, Dict], regime: str) -> Dict:
        features = self._compute_features(history)
        signal = {s: self._signal(f, regime) for s, f in features.items()}

        pnl_est = float(np.mean(list(-np.abs(list(signal.values())))))
        vol_est = float(np.std(list(signal.values())))

        return {
            "features": features,
            "signal": signal,
            "pnl_estimate": pnl_est,
            "vol_estimate": vol_est,
        }
