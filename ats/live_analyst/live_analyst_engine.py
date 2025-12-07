from __future__ import annotations

from typing import Any, Dict, List

from .live_feature_engine import LiveFeatureEngine
from .live_signal_router import LiveSignalRouter
from .live_strategy_adapter import LiveStrategyAdapter


class LiveAnalystEngine:
    """Full real-time analyst pipeline:

    UBF merged bar →
    LiveFeatureEngine →
    12-strategy LiveStrategyAdapter →
    LiveSignalRouter →
    Aggregator
    """

    def __init__(
        self,
        feature_engine: LiveFeatureEngine,
        strategy: LiveStrategyAdapter,
        router: LiveSignalRouter,
    ) -> None:
        self.feature_engine = feature_engine
        self.strategy = strategy
        self.router = router

    # ---------------------------
    # MAIN ENTRY POINT
    # ---------------------------
    def process(self, merged: Dict[str, Any]) -> List[Dict[str, Any]]:
        feats = self.feature_engine.build_features(merged)
        if feats is None:
            return []
        sigs = self.strategy.generate(feats)
        return self.router.route(sigs)
