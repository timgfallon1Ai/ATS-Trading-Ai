import json
from pathlib import Path
from typing import Any, Dict


class EquityCurveWriter:
    """Specialized lightweight writer just for equity curve emission.

    Backtester2 calls this on each bar:
        writer.append(timestamp, equity, cash, positions)

    The full results writer (results_writer.py) already writes equity too,
    but this class is intentionally separated so dashboards & real-time
    monitors can subscribe to only equity.
    """

    def __init__(self, root: str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

        self.path = self.root / "equity_curve.jsonl"

    def append(
        self, timestamp: int, equity: float, cash: float, positions: Dict[str, Any]
    ) -> None:
        payload = {
            "timestamp": timestamp,
            "equity": equity,
            "cash": cash,
            "positions": positions,
        }

        with open(self.path, "a") as f:
            f.write(json.dumps(payload) + "\n")
