from __future__ import annotations

from typing import Any, Dict, List


class LiveSignalRouter:
    """Merges multiple strategy signals into a single coherent list
    to be consumed by the live Aggregator.
    """

    def route(self, strategy_outputs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return strategy_outputs
