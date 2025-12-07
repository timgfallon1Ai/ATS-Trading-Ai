# ats/backtester2/position_intent.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class PositionIntent:
    """Analyst-aggregator output (intermediate before sizing).

    - symbol:    which ticker
    - strength:  continuous signal (-1..+1 typically)
    - raw_signals: list of dicts returned from strategies (for logging)

    Risk manager & position sizer use this canonical form.
    """

    symbol: str
    strength: float
    raw_signals: List[Dict[str, Any]] = field(default_factory=list)
