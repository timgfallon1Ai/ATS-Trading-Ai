# ats/backtester/event_queue.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, List, Dict
import heapq

@dataclass(order=True)
class Event:
    timestamp: float
    type: str
    data: Dict[str, Any]

class EventQueue:
    """
    Chronological event scheduler for the ATS backtester.
    Supports:
    - BAR events (Polygon OHLCV)
    - NEWS events (Benzinga)
    - CLOCK events (1-minute ticks)
    """

    def __init__(self):
        self._queue: List[Event] = []

    def push(self, timestamp: float, type: str, data: Dict[str, Any]):
        heapq.heappush(self._queue, Event(timestamp, type, data))

    def pop(self) -> Event | None:
        if not self._queue:
            return None
        return heapq.heappop(self._queue)

    def empty(self) -> bool:
        return len(self._queue) == 0
