from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class LiveRiskEnvelope:
    """A lightweight container representing the risk boundaries
    for a single symbol at the current moment.
    """

    max_position: float
    max_capital_risk: float
    require_confirmation: bool
    posture: str  # "normal", "cautious", "aggressive"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_position": self.max_position,
            "max_capital_risk": self.max_capital_risk,
            "require_confirmation": self.require_confirmation,
            "posture": self.posture,
        }
