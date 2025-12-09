from __future__ import annotations

from typing import Iterable, List

from .fill_types import Fill


class TradeLedger:
    """Append-only ledger of fills."""

    def __init__(self) -> None:
        self._fills: List[Fill] = []

    def record(self, fills: Iterable[Fill]) -> None:
        for fill in fills:
            self._fills.append(fill)

    def history(self) -> List[Fill]:
        """Return all recorded fills."""
        return list(self._fills)
