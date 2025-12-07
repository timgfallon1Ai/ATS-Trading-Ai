from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class GovernanceState:
    """Minimal state tracker for RM-7.
    Tracks posture transitions and risk metadata over time.
    """

    posture_history: List[Dict[str, Any]] = field(default_factory=list)
    risk_history: List[Dict[str, Any]] = field(default_factory=list)

    def record_event(
        self,
        symbol: str,
        posture: str,
        risk_score: float,
        timestamp: str,
    ):
        self.posture_history.append(
            {
                "symbol": symbol,
                "posture": posture,
                "timestamp": timestamp,
            }
        )
        self.risk_history.append(
            {
                "symbol": symbol,
                "risk_score": risk_score,
                "timestamp": timestamp,
            }
        )
