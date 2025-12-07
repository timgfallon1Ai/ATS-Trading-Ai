from __future__ import annotations

from typing import Dict

import numpy as np


class PatternRecognitionStrategy:
    """Z-Ultra Institutional Pattern Model (F2 Depth)

    Detects statistically significant price action patterns:
        - volatility compression (squeeze)
        - breakout bias / thrust continuation
        - reversal probability (doji, engulfing bodies)
        - wick imbalance analysis
        - volume confirmation signals
    """

    def __init__(self):
        pass

    def _compute_features(self, history: Dict[str, Dict]) -> Dict[str, Dict]:
        feats = {}

        for symbol, data in history.items():
            closes = np.array(data["close"][-80:])
            highs = np.array(data["high"][-80:])
            lows = np.array(data["low"][-80:])
            opens = np.array(data["open"][-80:])
            vols = np.array(data["volume"][-80:])

            # Volatility compression (Bollinger band width)
            bb_width = (highs[-20:].max() - lows[-20:].min()) / (closes[-1] + 1e-9)

            # Breakout probability
            breakout_score = (closes[-1] - highs[-20:].max()) / (
                np.std(closes[-20:]) + 1e-9
            )

            # Reversal: long upper/lower wick imbalance
            body = abs(closes[-1] - opens[-1])
            upper_wick = highs[-1] - max(closes[-1], opens[-1])
            lower_wick = min(closes[-1], opens[-1]) - lows[-1]

            wick_imbalance = (upper_wick - lower_wick) / (body + 1e-9)

            # Engulfing pattern detection
            prev_body = closes[-2] - opens[-2]
            engulf = 1.0 if abs(body) > abs(prev_body) * 1.2 else 0.0

            volume_surge = vols[-1] / (np.mean(vols[-20:]) + 1e-9)

            feats[symbol] = {
                "bb_width": bb_width,
                "breakout_score": breakout_score,
                "wick_imbalance": wick_imbalance,
                "engulf": engulf,
                "volume_surge": volume_surge,
                "pattern_strength": (
                    breakout_score * 0.4
                    + (-bb_width) * 0.2
                    + wick_imbalance * 0.15
                    + engulf * 0.15
                    + volume_surge * 0.1
                ),
            }

        return feats

    def _signal(self, f: Dict[str, float], regime: str) -> float:
        # Regime weighting — patterns break more reliably in trend regimes
        w = {
            "BULL": 1.4,
            "EXPANSION": 1.2,
            "NEUTRAL": 1.0,
            "VOLATILE": 0.7,
            "BEAR": -0.3,
            "CRISIS": -0.6,
        }[regime]

        return f["pattern_strength"] * w

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
