from typing import Dict


class RM4AnomalyDetector:
    """Anomaly detection based on:
    - volatility spikes
    - entropy surges
    - trend reversals
    - feature deviation from historical norms
    """

    def score(self, features: Dict) -> float:
        vol = features.get("rv_15", 0.0)
        entropy = features.get("entropy", 0.0)
        macd = features.get("macd_hist", 0.0)

        # Normalized components
        vol_score = min(1.0, vol * 10)
        entropy_score = min(1.0, entropy / 2)
        trend_reversal = min(1.0, abs(macd) * 2)

        anomaly = (vol_score * 0.4) + (entropy_score * 0.4) + (trend_reversal * 0.2)
        return float(max(0.0, min(anomaly, 1.0)))
