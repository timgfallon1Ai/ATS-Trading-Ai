# ats/backtester2/sim/fills.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Fill:
    """A simulated fill event produced by ExecutionEngine."""

    timestamp: float
    symbol: str
    qty: float
    price: float
