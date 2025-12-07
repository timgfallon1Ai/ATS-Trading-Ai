from __future__ import annotations

from typing import Any, Dict

from .allocation_engine import AllocationEngine
from .position_sizer import PositionSizer


class Aggregator:
    """Z-8 Aggregator Integration Layer

    Pipeline:
        Hybrid Analyst Output (H1-B)
            → PositionSizer (signal normalization + strength)
            → AllocationEngine (feature + meta assembly)
            → RM-MASTER batch input
    """

    def __init__(self):
        self.sizer = PositionSizer()
        self.engine = AllocationEngine()

    def aggregate(
        self,
        analyst_output: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        """analyst_output structure (from Hybrid Analyst Engine):

        {
            "AAPL": {
                "features": FeatureMap,
                "signal": float,
                "strategy_breakdown": {strategy: contribution},
                "meta": {
                    "pnl_estimate": float,
                    "vol_estimate": float,
                },
            },
            ...
        }

        Returns RM-MASTER batch input.
        """
        output: Dict[str, Dict[str, Any]] = {}

        # Step 1: normalize signals → strengths
        sized = self.sizer.size(analyst_output)

        # Step 2: build RM-ready allocation objects
        for symbol, payload in sized.items():
            alloc = self.engine.build(symbol=symbol, data=payload)
            output[symbol] = alloc

        return output
