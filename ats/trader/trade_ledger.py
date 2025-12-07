from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, List

from ats.trader.fill_types import Fill


@dataclass
class TradeRecord:
    """
    Immutable record of a completed trade event.

    `realized_pnl` is the P&L attributed to this fill.
    """

    symbol: str
    side: str
    size: float
    price: float
    timestamp: Any  # datetime, but kept generic for serialization
    realized_pnl: float


class TradeLedger:
    """
    In-memory trade journal.

    Thin, append-only. Use `to_dicts()` when you want to serialize.
    """

    def __init__(self) -> None:
        self.records: List[TradeRecord] = []

    def record(self, fill: Fill, realized_pnl: float) -> None:
        """Append a new trade record."""
        self.records.append(
            TradeRecord(
                symbol=fill.symbol,
                side=fill.side,
                size=fill.size,
                price=fill.price,
                timestamp=fill.timestamp,
                realized_pnl=realized_pnl,
            )
        )

    def to_dicts(self) -> List[dict]:
        """Return a list of plain dicts suitable for JSON/CSV."""
        return [asdict(r) for r in self.records]
