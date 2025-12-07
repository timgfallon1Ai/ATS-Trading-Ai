# ats/backtester2/bt_trace.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class TraceEvent:
    ts: int
    symbol: str | None
    stage: str
    payload: Dict[str, Any]


class BTTrace:
    """Lightweight event recorder for debugging and bar-by-bar tracing."""

    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.events: List[TraceEvent] = []

    def log(
        self, ts: int, stage: str, payload: Dict[str, Any], symbol: str | None = None
    ):
        if not self.enabled:
            return

        evt = TraceEvent(ts=ts, stage=stage, symbol=symbol, payload=payload)
        self.events.append(evt)

    def dump(self) -> List[TraceEvent]:
        return self.events

    def clear(self):
        self.events.clear()
