from __future__ import annotations

from typing import Any, Dict


class VolatilityGuard:
    """Detects short-term volatility spikes that require risk tightening
    or strategy throttling.
    """

    def __init__(self, threshold: float = 0.015) -> None:
        self.threshold = threshold

    def spike_detected(self, merged: Dict[str, Any]) -> bool:
        price = merged.get("price")
        if not price:
            return False

        high = float(price["high"])
        low = float(price["low"])
        mid = (high + low) / 2
        if mid == 0:
            return False

        vol = (high - low) / mid
        return vol > self.threshold
