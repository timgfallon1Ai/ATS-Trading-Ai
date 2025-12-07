from __future__ import annotations

from .features import FeatureSchema, FeatureVector


class FeatureEngine:
    """Extracts a consistent feature vector from any unified bar (UBF).
    All analyst strategies consume feature vectors only.
    """

    def __init__(self):
        self.schema: FeatureSchema = {
            "feature_names": [
                "open",
                "high",
                "low",
                "close",
                "volume",
                "returns_1m",
                "volatility_5m",
                "momentum_5m",
            ]
        }

    def extract(self, symbol: str, bar: dict) -> FeatureVector:
        """Convert a UBF bar → FeatureVector."""
        return {
            "symbol": symbol,
            "features": {
                "open": bar["open"],
                "high": bar["high"],
                "low": bar["low"],
                "close": bar["close"],
                "volume": bar["volume"],
                "returns_1m": bar.get("returns_1m", 0.0),
                "volatility_5m": bar.get("volatility_5m", 0.0),
                "momentum_5m": bar.get("momentum_5m", 0.0),
            },
        }

    def get_schema(self) -> FeatureSchema:
        return self.schema
