from typing import Dict


class RegimeClassifier:
    """RM-2 Regime classification using:
    - volatility levels
    - return slope
    - entropy
    - MACD histogram
    """

    def classify(self, features: Dict) -> str:
        vol = features.get("rv_15", 0.0)
        entropy = features.get("entropy", 0.0)
        macd_hist = features.get("macd_hist", 0.0)
        r60 = features.get("return_60", 0.0)

        if vol < 0.01 and entropy < 0.5:
            return "low_vol"

        if vol < 0.02 and macd_hist > 0 and r60 > 0:
            return "mid_vol_uptrend"

        if vol < 0.02 and macd_hist < 0 and r60 < 0:
            return "mid_vol_downtrend"

        if vol >= 0.02 and entropy < 1.0:
            return "high_vol_structured"

        return "high_vol_chaotic"
