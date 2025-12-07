from __future__ import annotations

from typing import Dict, List, TypedDict


class FeatureVector(TypedDict):
    """A single feature vector for one asset."""

    symbol: str
    features: Dict[str, float]


class FeatureSchema(TypedDict):
    """Schema describing all feature names."""

    feature_names: List[str]
