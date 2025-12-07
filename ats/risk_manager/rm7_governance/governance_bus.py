from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class GovernanceEvent:
    """Single governance event emitted anywhere in ATS."""

    timestamp: str
    symbol: str
    stage: str
    message: str
    details: Dict[str, Any]


class GovernanceBus:
    """Minimal RM-7 Governance Event Bus
    Collects posture transitions, RM rule violations, allocation notes,
    execution warnings, etc.
    """

    def __init__(self):
        self.events: List[GovernanceEvent] = []

    def push_event(
        self,
        symbol: str,
        stage: str,
        message: str,
        details: Dict[str, Any] | None = None,
    ):
        evt = GovernanceEvent(
            timestamp=datetime.utcnow().isoformat(),
            symbol=symbol,
            stage=stage,
            message=message,
            details=details or {},
        )
        self.events.append(evt)

    def flush(self) -> List[GovernanceEvent]:
        """Return and clear accumulated events (used by orchestrator logger)."""
        out = list(self.events)
        self.events.clear()
        return out
