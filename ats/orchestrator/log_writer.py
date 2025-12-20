from __future__ import annotations

import json
import traceback
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{uuid.uuid4().hex[:8]}"


@dataclass(frozen=True)
class LogPaths:
    base_dir: Path
    run_dir: Path
    events_file: Path


class LogWriter:
    """Structured JSONL logger used by ats.run.

    Record shape:
        {
          "ts": "...",
          "run_id": "...",
          "seq": 1,
          "level": "info" | "error" | "debug",
          "event": "session_start" | ...,
          "data": { ... }
        }
    """

    def __init__(
        self,
        log_dir: str | Path = "logs",
        run_id: Optional[str] = None,
        filename: str = "events.jsonl",
    ) -> None:
        base = Path(log_dir)

        # If a file named "logs" exists (historic repo artifact), avoid crashing.
        if base.exists() and base.is_file():
            base = base.with_name(base.name + "_dir")

        base.mkdir(parents=True, exist_ok=True)

        self._run_id = run_id or default_run_id()
        run_dir = base / self._run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        self._paths = LogPaths(
            base_dir=base,
            run_dir=run_dir,
            events_file=run_dir / filename,
        )
        self._seq = 0

    @property
    def run_id(self) -> str:
        return self._run_id

    @property
    def paths(self) -> LogPaths:
        return self._paths

    def emit(
        self,
        event: str,
        data: Dict[str, Any] | None = None,
        level: str = "info",
    ) -> None:
        self._seq += 1
        payload = {
            "ts": _utc_now_iso(),
            "run_id": self._run_id,
            "seq": self._seq,
            "level": level,
            "event": event,
            "data": data or {},
        }

        with self._paths.events_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    # ---------------------------------------------------------------------
    # Backwards-compatible API (older code uses `write` and `write_many`)
    # ---------------------------------------------------------------------
    def write(self, record_type: str, payload: Dict[str, Any]) -> None:
        self.emit(event=record_type, data=payload, level="info")

    def write_many(self, record_type: str, items: list[Dict[str, Any]]) -> None:
        for item in items:
            self.write(record_type, item)

    def exception(
        self,
        event: str,
        data: Dict[str, Any] | None = None,
        exc: BaseException | None = None,
    ) -> None:
        """Emit an error event including exception metadata."""
        if exc is None:
            tb = traceback.format_exc()
            exc_type = None
            exc_msg = None
        else:
            tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            exc_type = type(exc).__name__
            exc_msg = str(exc)

        merged = dict(data or {})
        merged.update(
            {
                "exc_type": exc_type,
                "exc_msg": exc_msg,
                "traceback": tb,
            }
        )
        self.emit(event=event, data=merged, level="error")
