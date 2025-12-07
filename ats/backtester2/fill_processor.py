# ats/backtester2/fill_processor.py

from __future__ import annotations

from typing import Any, Dict, List


class FillProcessor:
    """Normalizes raw execution fills for backtesting.

    Execution engines (simulation or live) may return data differently,
    so we convert everything into a canonical fill format the ledger can use.
    """

    def __init__(self):
        pass

    def normalize_fill(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Raw example formats:

        Simulation:
            {"symbol": "AAPL", "qty": 10, "price": 187.32, "timestamp": 1690000000}

        Live broker:
            {"symbol": "AAPL", "filled": 10, "avg_price": 187.32, "ts": 1690000000}

        This function outputs a unified canonical fill format:
        {
            "symbol": str,
            "qty": int,
            "price": float,
            "timestamp": int,
        }
        """
        # Detect numeric timestamp
        ts = raw.get("timestamp") or raw.get("ts") or raw.get("time")

        return {
            "symbol": raw.get("symbol"),
            "qty": raw.get("qty") or raw.get("filled") or 0,
            "price": raw.get("price") or raw.get("avg_price") or 0.0,
            "timestamp": int(ts) if ts is not None else 0,
        }

    def process_fills(self, raw_fills: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize many fills in a batch."""
        return [self.normalize_fill(r) for r in raw_fills]
