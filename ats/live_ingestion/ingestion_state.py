from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class StreamState:
    last_timestamp: Optional[int] = None
    connected: bool = False
    errors: int = 0


@dataclass
class IngestionState:
    symbols: Dict[str, StreamState] = field(default_factory=dict)

    def ensure_symbol(self, symbol: str) -> None:
        if symbol not in self.symbols:
            self.symbols[symbol] = StreamState()

    def update_timestamp(self, symbol: str, ts: int) -> None:
        self.ensure_symbol(symbol)
        self.symbols[symbol].last_timestamp = ts

    def mark_connected(self, symbol: str) -> None:
        self.ensure_symbol(symbol)
        self.symbols[symbol].connected = True

    def mark_error(self, symbol: str) -> None:
        self.ensure_symbol(symbol)
        self.symbols[symbol].errors += 1
