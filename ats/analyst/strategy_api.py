from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

FeatureRow = Dict[str, float]


@dataclass
class StrategySignal:
    """Unified output from a single strategy.

    Attributes
    ----------
    symbol:
        Ticker the signal applies to.
    strategy_name:
        Human-readable strategy identifier.
    score:
        Directional conviction in [-1, 1].
        -1 = strong short, 0 = neutral, +1 = strong long.
    confidence:
        Weight in [0, 1] used when aggregating across strategies.
    metadata:
        Optional strategy-specific diagnostics.
    """

    symbol: str
    strategy_name: str
    score: float
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def normalized(self) -> "StrategySignal":
        """Return a copy with score / confidence clipped to valid ranges."""
        score = max(-1.0, min(1.0, float(self.score)))
        confidence = max(0.0, min(1.0, float(self.confidence)))
        return StrategySignal(
            symbol=self.symbol,
            strategy_name=self.strategy_name,
            score=score,
            confidence=confidence,
            metadata=dict(self.metadata),
        )
