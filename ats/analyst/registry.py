"""Global Strategy Registry

This is the central registry for all strategies in Option A architecture.

Strategies are registered automatically via the @register_strategy("name")
decorator inside strategy_base.py.

The AnalystEngine will instantiate strategies from this registry at runtime.

This file MUST remain extremely stable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Type

from .strategy_base import Strategy


# =====================================================================
# Registry Storage Class
# =====================================================================
@dataclass
class StrategyRegistry:
    """Holds a mapping of:
        name (str) → class (subclass of Strategy)

    This class performs:
        - registration validation
        - duplicate checking
        - safe retrieval for AnalystEngine
    """

    registry: Dict[str, Type[Strategy]]

    # ---------------------------------------------------------------
    def __init__(self) -> None:
        self.registry = {}

    # ---------------------------------------------------------------
    def register(self, name: str, cls: Type[Strategy]) -> None:
        """Registers a strategy class under a given name."""
        if name in self.registry:
            raise RuntimeError(f"Strategy '{name}' already registered.")

        if not issubclass(cls, Strategy):
            raise TypeError(f"Class {cls.__name__} must extend Strategy.")

        self.registry[name] = cls

    # ---------------------------------------------------------------
    def create(self, name: str) -> Strategy:
        """Instantiates a strategy by name.

        Example:
            strat = registry.create("mean_reversion")

        """
        if name not in self.registry:
            raise KeyError(f"Strategy '{name}' not found.")

        cls = self.registry[name]
        return cls(name)

    # ---------------------------------------------------------------
    def list_strategies(self) -> Dict[str, Type[Strategy]]:
        """Returns the internal registry for metadata/UI."""
        return dict(self.registry)


# =====================================================================
# Global Singleton
# =====================================================================

strategy_registry = StrategyRegistry()
