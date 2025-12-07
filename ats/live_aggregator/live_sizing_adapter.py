from __future__ import annotations

from typing import Any, Dict


class LiveSizingAdapter:
    """Converts risk envelope + strategy scores into final position sizes."""

    def size(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        risk = signal["risk"]
        score = float(signal.get("score", 1.0))

        # Max position allowed
        max_pos = risk["max_position"]

        # Score-weighted allocation
        size = max_pos * score

        out = signal.copy()
        out["final_size"] = size
        return out
