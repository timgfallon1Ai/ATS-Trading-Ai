from typing import Dict


class VolatilityModel:
    """RM-2 Volatility Forecasting Model.

    Forecasts volatility using:
    - realized volatility windows
    - entropy (market randomness)
    - autocorrelation features
    """

    def forecast(self, features: Dict) -> float:
        rv5 = features.get("rv_5", 0.0)
        rv15 = features.get("rv_15", 0.0)
        rv60 = features.get("rv_60", 0.0)
        entropy = features.get("entropy", 0.0)

        # Blend realized volatility horizons
        base_vol = (rv5 * 0.5) + (rv15 * 0.3) + (rv60 * 0.2)

        # Increase forecast in chaotic regimes
        chaos_adjustment = min(0.5, entropy * 0.1)

        expected_vol = base_vol * (1 + chaos_adjustment)
        return float(max(0.0001, expected_vol))  # prevent zero volatility
