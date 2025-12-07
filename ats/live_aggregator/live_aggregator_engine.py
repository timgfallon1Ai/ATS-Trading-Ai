from __future__ import annotations

from typing import Any, Dict, List

from ats.live_risk.live_risk_orchestrator import LiveRiskOrchestrator

from .live_allocation_engine import LiveAllocationEngine


class LiveAggregatorEngine:
    """Full real-time aggregation:

    strategy_signals →
    risk_orchestrator →
    sizing/allocation →
    final trade intents for Trader
    """

    def __init__(
        self, risk_orchestrator: LiveRiskOrchestrator, allocation: LiveAllocationEngine
    ) -> None:
        self.risk = risk_orchestrator
        self.allocation = allocation

    def process(
        self, merged: Dict[str, Any], strategy_signals: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        risk_filtered = self.risk.process(merged, strategy_signals)
        return self.allocation.allocate(risk_filtered)
