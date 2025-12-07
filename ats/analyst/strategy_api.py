from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class FeatureVector:
    """A normalized, validated feature set produced by FeatureEngine.
    Keys: str feature names
    Values: float values
    """

    values: Dict[str, float]


@dataclass
class StrategySignal:
    """Unified output format for all strategy modules.
    strategy: name of the strategy, e.g. "momentum"
    symbol:   trading symbol
    score:    raw score or probability
    metadata: debug / intermediate data
    """

    strategy: str
    symbol: str
    score: float
    metadata: Dict[str, Any]


@dataclass
class StrategyConfig:
    """Formal configuration for each strategy, allowing
    different thresholds / lookbacks / modes.
    """

    name: str
    params: Dict[str, Any]


class Strategy:
    """Base interface for all ATS strategies.

    Each strategy MUST implement:
        - generate()
    """

    def __init__(self, config: StrategyConfig):
        self.config = config

    def generate(self, symbol: str, features: FeatureVector) -> List[StrategySignal]:
        """Produce one or more signals for a symbol.
        Returned values MUST be StrategySignal instances.
        """
        raise NotImplementedError
