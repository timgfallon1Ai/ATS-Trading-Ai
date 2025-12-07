"""Strategy Base Class (Option A Architecture)

All strategies must:
    - Inherit from Strategy
    - Implement generate_signal(self, features)
    - Use @register_strategy("name") decorator

This file provides:
    - Strong typing
    - Safe required interface
    - Lightweight runtime guards
    - No circular imports
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


# =====================================================================
# StrategySignal — standard normalized signal object
# =====================================================================
@dataclass
class StrategySignal:
    """Unified signal structure. Every strategy must return either:

        StrategySignal(
            symbol="AAPL",
            timestamp=1700000000,
            score=0.63,
            meta={ "window": 20, "zscore": -1.2 }
        )

    Or None (no signal).
    """

    symbol: str
    timestamp: int
    score: float  # normalized [-1, 1]
    meta: Dict[str, Any]


# =====================================================================
# Strategy Base
# =====================================================================
class Strategy(ABC):
    """Abstract base strategy class.
    Every subclass must implement `generate_signal`.

    No strategy should override __init__ unless absolutely necessary.
    """

    def __init__(self, name: str):
        self.name = name

    # ---------------------------------------------------------------
    @abstractmethod
    def generate_signal(self, features: Dict[str, Any]) -> Optional[StrategySignal]:
        """Main strategy method.

        Parameters
        ----------
            features: Dict[str, Any]
                Arbitrary feature dict supplied by AnalystEngine.

        Returns
        -------
            StrategySignal | None

        """
        raise NotImplementedError

    # ---------------------------------------------------------------
    def _validate_signal(self, signal: StrategySignal) -> None:
        """Optional safety validator.
        Called by AnalystEngine before passing to downstream systems.
        """
        if not isinstance(signal.symbol, str):
            raise ValueError("signal.symbol must be str")

        if not isinstance(signal.timestamp, int):
            raise ValueError("signal.timestamp must be int")

        if not isinstance(signal.score, (int, float)):
            raise ValueError("signal.score must be a number")

        if signal.score < -1 or signal.score > 1:
            raise ValueError("signal.score must be in range [-1, 1]")


# =====================================================================
# Decorator + registry binding
# =====================================================================
# The registry is imported locally to avoid circular imports.
def register_strategy(name: str):
    """Decorator used by all strategies to bind themselves to the global
    StrategyRegistry. Example:

        @register_strategy("mean_reversion")
        class MeanReversionStrategy(Strategy):
            ...

    """

    def decorator(cls):
        from .registry import strategy_registry  # local import avoids circular import

        if not issubclass(cls, Strategy):
            raise TypeError(f"{cls.__name__} must subclass Strategy")

        strategy_registry.register(name, cls)
        return cls

    return decorator
