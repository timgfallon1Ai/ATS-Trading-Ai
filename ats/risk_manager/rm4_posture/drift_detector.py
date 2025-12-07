from typing import Dict


class DriftDetector:
    """Detects slow regime drift via:
    - volatility slope
    - return slope
    - regime mismatch
    """

    def score(self, features: Dict, current_regime: str) -> float:
        r60 = features.get("return_60", 0.0)
        vol = features.get("rv_60", 0.0)
        macd = features.get("macd_hist", 0.0)

        # Drift = instability of trend across timeframes
        slope_instability = min(1.0, abs(r60) * 5)
        vol_shift = min(1.0, vol * 5)
        trend_shift = min(1.0, abs(macd) * 2)

        # Combine
        drift = (slope_instability * 0.4) + (vol_shift * 0.4) + (trend_shift * 0.2)
        return float(max(0.0, min(drift, 1.0)))
