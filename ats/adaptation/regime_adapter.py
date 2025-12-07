class RegimeAdapter:
    """Market Regime → Weight Adjustment"""

    def __init__(self):
        self.vol_thresholds = {"low": 0.01, "medium": 0.02, "high": 0.04}

    def classify(self, vol: float) -> str:
        if vol < self.vol_thresholds["low"]:
            return "LOW_VOL"
        if vol < self.vol_thresholds["medium"]:
            return "MEDIUM_VOL"
        return "HIGH_VOL"

    def adjust(self, weights, regime: str):
        out = {}

        for s, w in weights.items():
            if regime == "LOW_VOL":
                out[s] = w * 1.1
            elif regime == "HIGH_VOL":
                out[s] = w * 0.8
            else:
                out[s] = w

        return out
