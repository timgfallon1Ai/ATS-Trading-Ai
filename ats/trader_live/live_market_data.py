from __future__ import annotations

import time
from typing import Any, Callable, Dict


class LiveMarketData:
    """Thin live market data abstraction.
    The caller provides a function `fetch(symbol)` returning an OHLC snapshot.
    """

    def __init__(self, fetch_fn: Callable[[str], Dict[str, Any]]):
        self.fetch_fn = fetch_fn

    def get(self, symbol: str) -> Dict[str, Any]:
        data = self.fetch_fn(symbol)
        data["timestamp"] = time.time()
        return data
