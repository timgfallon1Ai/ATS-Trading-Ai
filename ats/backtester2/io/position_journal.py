import json
from pathlib import Path
from typing import Any, Dict


class PositionJournal:
    """Position state journal.

    Emits a record AFTER the Trader/Portfolio applies fills and RM constraints.

    Each JSONL entry contains:
        {
            "timestamp": int,
            "positions": {
                "AAPL": {"qty": 50, "avg_price": 188.32},
                "MSFT": {"qty": -20, "avg_price": 421.87},
                ...
            },
            "cash": float,
            "equity": float,
            "exposure_long": float,
            "exposure_short": float,
            "gross_exposure": float,
            "net_exposure": float
        }
    """

    def __init__(self, root: str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "positions.jsonl"

    def append(self, payload: Dict[str, Any]) -> None:
        with open(self.path, "a") as f:
            f.write(json.dumps(payload) + "\n")
