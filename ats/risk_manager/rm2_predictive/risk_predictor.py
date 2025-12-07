from typing import Dict

from .regime_classifier import RegimeClassifier
from .volatility_model import VolatilityModel


class RiskPredictor:
    """RM-2 Predictive Risk Engine.

    Produces:
    - expected_volatility
    - regime classification
    - predictive_risk score
    - risk_multiplier (used by RM-3 and RM-4)
    """

    def __init__(self):
        self.vol_model = VolatilityModel()
        self.regimes = RegimeClassifier()

    def predict(self, features: Dict) -> Dict:
        expected_vol = self.vol_model.forecast(features)
        regime = self.regimes.classify(features)

        r15 = features.get("return_15", 0.0)
        entropy = features.get("entropy", 0.0)
        macd_hist = features.get("macd_hist", 0.0)

        # Predictive risk score:
        # Combines volatility, entropy, and trend instability
        predictive_risk = expected_vol * 0.6 + abs(macd_hist) * 0.2 + entropy * 0.2

        # Convert predictive risk → multiplier in [0.3, 1.0]
        risk_multiplier = max(0.3, 1.0 - predictive_risk)

        return {
            "expected_volatility": float(expected_vol),
            "regime": regime,
            "predictive_risk": float(predictive_risk),
            "risk_multiplier": float(risk_multiplier),
        }
