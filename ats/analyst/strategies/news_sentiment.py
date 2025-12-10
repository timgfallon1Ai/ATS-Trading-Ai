from __future__ import annotations

from typing import Dict

import numpy as np


class NewsSentimentStrategy:
    """Z-Ultra Sentiment Model (F2 Depth)

    Placeholder internal sentiment engine until live news streams
    (Benzinga / Polygon / Twitter / IBKR) are connected.

    Computes:
        - price reaction to prior volatility (proxy for sentiment)
        - overnight gap sentiment
        - momentum shock index
        - volatility-adjusted drift
    """

    def __init__(self):
        pass

    def _compute_features(self, history: Dict[str, Dict]) -> Dict[str, Dict]:
        feats = {}

        for symbol, data in history.items():
            closes = np.array(data["close"][-60:])
            opens = np.array(data["open"][-60:])

            ret = closes[-1] - closes[-2]
            vol20 = np.std(closes[-20:])
            overnight_gap = (opens[-1] - closes[-2]) / (closes[-2] + 1e-9)

            shock_index = ret / (vol20 + 1e-9)

            drift = np.mean(np.diff(closes[-10:]))

            feats[symbol] = {
                "overnight_gap": overnight_gap,
                "shock_index": shock_index,
                "drift": drift,
                "sent_strength": (
                    overnight_gap * 0.4 + shock_index * 0.4 + drift * 0.2
                ),
            }

        return feats

    def _signal(self, f: Dict[str, float], regime: str) -> float:
        # Sentiment is more powerful in trend regimes
        w = {
            "BULL": 1.5,
            "EXPANSION": 1.2,
            "NEUTRAL": 0.9,
            "VOLATILE": 0.7,
            "BEAR": -0.4,
            "CRISIS": -0.8,
        }[regime]

        return f["sent_strength"] * w

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
