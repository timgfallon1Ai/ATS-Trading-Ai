from __future__ import annotations

from typing import Any, Dict, Optional


class CrossSymbolMemory:
    """Stores rolling context for all symbols,
    enabling multi-symbol & cross-asset strategies.
    """

    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, Any]] = {}

    def update(self, symbol: str, merged: Dict[str, Any]) -> None:
        self._store[symbol] = merged

    def get(self, symbol: str) -> Optional[Dict[str, Any]]:
        return self._store.get(symbol)

    def all_symbols(self) -> Dict[str, Dict[str, Any]]:
        return self._store
