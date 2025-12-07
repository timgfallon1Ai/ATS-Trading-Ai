from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class LogWriter:
    """
    Unified ATS logging layer.
    Writes governance events, risk packets, and trader fills to rotating JSONL files.
    """

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------
    def _file(self) -> Path:
        """Daily log file."""
        date = datetime.utcnow().strftime("%Y-%m-%d")
        return self.log_dir / f"{date}.jsonl"

    # ------------------------------------------------------------
    def write(self, record_type: str, payload: Dict[str, Any]):
        """
        Writes a single log line:
        {
            "ts": "...",
            "type": "governance" | "risk" | "trade",
            "data": { ... }
        }
        """
        entry = {
            "ts": datetime.utcnow().isoformat(),
            "type": record_type,
            "data": payload,
        }

        with self._file().open("a") as f:
            f.write(json.dumps(entry) + "\n")

    # ------------------------------------------------------------
    def write_many(self, record_type: str, items: List[Dict[str, Any]]):
        """Write multiple events at once."""
        for item in items:
            self.write(record_type, item)
