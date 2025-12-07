import json
from pathlib import Path
from typing import Any, Dict


class BacktestManifest:
    """The single authoritative descriptor for a backtest run.

    Contains:
        - run_id
        - engine_version
        - analyst_version
        - rm_version
        - trader_version
        - timestamp_start
        - timestamp_end
        - symbols
        - bar_count
        - notes (optional user comments)

    Written once at the start of a run.
    """

    def __init__(self, root: str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "manifest.json"

    def write(self, payload: Dict[str, Any]) -> None:
        with open(self.path, "w") as f:
            json.dump(payload, f, indent=2)
