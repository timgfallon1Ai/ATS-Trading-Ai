from __future__ import annotations

from typing import Any, Dict


class AllocationEngine:
    """Converts sized signals → RM-MASTER allocations.

    Output schema must match AggregatedAllocation:
    {
        "symbol": str,
        "raw_signal": float,
        "strength": float,
        "strategy_breakdown": Dict[str, float],
        "features": Dict[str, Any],
        "meta": Dict[str, Any],
    }
    """

    def build(self, symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "symbol": symbol,
            "raw_signal": data["signal"],
            "strength": data["strength"],
            "strategy_breakdown": data.get("strategy_breakdown", {}),
            "features": data["features"],
            "meta": data.get("meta", {}),
        }
