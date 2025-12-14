# ats/analyst/feature_schema.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class FeatureSpec:
    """
    Declarative definition of a single feature.

    The meaning of `window` is left to the FeatureEngine implementation.
    """

    name: str
    description: str = ""
    window: int = 1


class FeatureSchema:
    """
    Central registry of available features.

    This keeps feature naming consistent across strategies and engines.
    """

    def __init__(self) -> None:
        self._features: Dict[str, FeatureSpec] = {}

    def register(self, spec: FeatureSpec) -> None:
        self._features[spec.name] = spec

    def get(self, name: str) -> FeatureSpec:
        return self._features[name]

    def all(self) -> List[FeatureSpec]:
        return list(self._features.values())


def default_feature_schema() -> FeatureSchema:
    """
    Base feature set for v1 of the ATS.

    This is intentionally modest; we can extend it over time
    without breaking the contract.
    """
    schema = FeatureSchema()

    schema.register(
        FeatureSpec(
            name="close",
            description="Last traded price for the bar.",
            window=1,
        )
    )
    schema.register(
        FeatureSpec(
            name="vwap",
            description="Volume-weighted average price for the bar.",
            window=1,
        )
    )
    schema.register(
        FeatureSpec(
            name="ma_fast",
            description="Fast moving average of closing price.",
            window=20,
        )
    )
    schema.register(
        FeatureSpec(
            name="ma_slow",
            description="Slow moving average of closing price.",
            window=50,
        )
    )
    schema.register(
        FeatureSpec(
            name="volatility_20",
            description="Rolling volatility over 20 bars.",
            window=20,
        )
    )

    return schema
