from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class LogWriter:
    """
    Simple JSONL event logger.

    Creates:
      <log_dir>/<run_id>/events.jsonl
    """

    def __init__(self, log_dir: Path, run_id: str) -> None:
        self.log_dir = Path(log_dir)
        self.run_id = str(run_id)

        # Run directory
        self.path = self.log_dir / self.run_id
        self.path.mkdir(parents=True, exist_ok=True)

        # Events file
        self.events_path = self.path / "events.jsonl"
        self.events_path.touch(exist_ok=True)

    def event(self, name: str, meta: Optional[Dict[str, Any]] = None) -> None:
        record: Dict[str, Any] = {"ts": _utc_now_iso(), "event": str(name)}
        if meta is not None:
            record["meta"] = meta

        with self.events_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
