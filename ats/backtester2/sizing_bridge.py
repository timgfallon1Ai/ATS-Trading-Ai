# ats/backtester2/sizing_bridge.py

from __future__ import annotations

from typing import List

from ats.aggregator.position_sizer import PositionSizer
from ats.backtester2.position_intent import PositionIntent


class SizingBridge:
    """Converts PositionIntent -> sized trade instructions using PositionSizer.
    Backtester and Trader both use this bridge.
    """

    def __init__(self, sizer: PositionSizer):
        self.sizer = sizer

    def size(self, intents: List[PositionIntent], portfolio_state) -> List[dict]:
        """Returns list of order instructions in canonical ATS format:

        {
            "symbol": "AAPL",
            "target_qty": 42,
            "reason": "signals + rm",
            "strength": 0.73,
        }
        """
        if not intents:
            return []

        return self.sizer.size_positions(
            intents=intents,
            portfolio_state=portfolio_state,
        )
