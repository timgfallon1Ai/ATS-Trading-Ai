# ats/backtester2/time_context.py

from __future__ import annotations

from datetime import datetime
from typing import Dict

from .interfaces import TimeContext, UBFBar


def build_time_context(bars: Dict[str, UBFBar]) -> TimeContext:
    """Takes the dict of bars from the iterator and computes
    a consistent time context (timestamp + datetime).
    Uses the *latest* timestamp in the batch.
    """
    ts = max(int(b["timestamp"]) for b in bars.values())
    return {
        "timestamp": ts,
        "datetime": datetime.utcfromtimestamp(ts / 1000.0),
    }
