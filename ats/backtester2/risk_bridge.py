# ats/backtester2/risk_bridge.py

from __future__ import annotations

from typing import List

from ats.backtester2.position_intent import PositionIntent
from ats.risk_manager.risk_manager import RiskManager


class RiskBridge:
    """Converts PositionIntent -> PositionIntent after risk approval.

    This file is intentionally thin because the RM stack is complex and modular.
    """

    def __init__(self, rm: RiskManager):
        self.rm = rm

    def review(self, intents: List[PositionIntent]) -> List[PositionIntent]:
        """Pass intents into RM for evaluation.

        RM returns a filtered / adjusted list.
        """
        if not intents:
            return []

        return self.rm.apply(intents)
