from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict


@dataclass
class PortfolioSnapshot:
    """
    Minimal portfolio snapshot for backtests.

    Captures a point-in-time view of:
    - timestamp
    - total equity
    - cash
    - realized PnL
    - per-symbol positions
    """

    timestamp: datetime
    equity: float
    cash: float
    realized_pnl: float
    positions: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        """Return a JSON-serializable representation."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "equity": self.equity,
            "cash": self.cash,
            "realized_pnl": self.realized_pnl,
            "positions": dict(self.positions),
        }
