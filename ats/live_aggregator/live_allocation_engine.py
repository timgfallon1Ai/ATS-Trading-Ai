from __future__ import annotations

from typing import Any, Dict, List

from .live_sizing_adapter import LiveSizingAdapter


class LiveAllocationEngine:
    """Produces final trade intents:

    [
        { "symbol": "AAPL", "final_size": 13.4, "side": "buy" },
        ...
    ]
    """

    def __init__(self, sizing: LiveSizingAdapter) -> None:
        self.sizing = sizing

    def allocate(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for sig in signals:
            enriched = self.sizing.size(sig)
            out.append(enriched)
        return out
