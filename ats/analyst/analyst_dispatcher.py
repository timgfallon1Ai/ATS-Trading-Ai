# ats/analyst/analyst_dispatcher.py
from __future__ import annotations

from typing import List, Mapping, Optional, Sequence

from .analyst_engine import AnalystEngine
from .feature_engine import FeatureEngine
from .registry import create_strategies
from .strategy_api import StrategySignal, StrategyConfig


class AnalystDispatcher:
    """
    High-level façade for the analyst layer.

    In backtest mode, this can be constructed with a simple strategy config.
    In live mode, it can later be wired into the orchestrator.
    """

    def __init__(
        self,
        strategy_config: Mapping[str, StrategyConfig],
        feature_engine: Optional[FeatureEngine] = None,
    ) -> None:
        self._strategies = create_strategies(strategy_config)
        self._engine = AnalystEngine(self._strategies, feature_engine=feature_engine)

    @property
    def engine(self) -> AnalystEngine:
        return self._engine

    def on_startup(self) -> None:
        self._engine.on_startup()

    def on_shutdown(self) -> None:
        self._engine.on_shutdown()

    def evaluate_bar(
        self,
        timestamp: str,
        universe: Sequence[str],
        prices: Mapping[str, float],
        risk_state: Optional[Mapping[str, object]] = None,
    ) -> List[StrategySignal]:
        """
        Convenience wrapper around AnalystEngine.evaluate_bar.
        """
        return self._engine.evaluate_bar(
            timestamp=timestamp,
            universe=universe,
            prices=prices,
            risk_state=risk_state,
        )
