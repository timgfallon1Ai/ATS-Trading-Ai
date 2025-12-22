from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional


def _utc_now_iso() -> str:
    # Always UTC, always timezone-aware
    return datetime.now(timezone.utc).isoformat()


def _default_run_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{ts}-{uuid.uuid4().hex[:8]}"


class LogWriter:
    """
    Unified ATS JSONL logger.

    Design goals:
    - Create run-scoped log directory: <log_dir>/<run_id>/events.jsonl
    - Provide a modern `.event(...)` API used by ats.run runtime orchestration
    - Keep backward compatibility with older `.write(...)` / `.write_many(...)` usage
    - Be resilient if `log_dir` is accidentally a FILE (rename out of the way)
    """

    def __init__(self, log_dir: str | Path = "logs", run_id: Optional[str] = None):
        base = Path(log_dir)

        # If someone accidentally created "logs" as a FILE, move it aside so we can mkdir.
        if base.exists() and base.is_file():
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            backup = base.with_name(f"{base.name}.file.{ts}")
            base.rename(backup)

        base.mkdir(parents=True, exist_ok=True)

        # Prefer explicit run_id, then env override, then generated.
        resolved_run_id = run_id or os.getenv("ATS_RUN_ID") or _default_run_id()

        self.base_dir: Path = base
        self.run_id: str = resolved_run_id
        self.run_dir: Path = self.base_dir / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)

        self.events_path: Path = self.run_dir / "events.jsonl"

    @property
    def path(self) -> Path:
        """Back-compat alias used by some callers."""
        return self.events_path

    def _append(self, entry: Mapping[str, Any]) -> None:
        # Ensure directory exists even if someone deleted it mid-run.
        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(dict(entry), ensure_ascii=False) + "\n")

    # ---------------------------------------------------------------------
    # New API (used by ats.run runtime)
    # ---------------------------------------------------------------------
    def event(
        self,
        event_type: str,
        *,
        meta: Optional[Mapping[str, Any]] = None,
        level: str = "INFO",
        **fields: Any,
    ) -> None:
        """
        Write a structured event.

        Example:
            log.event("session_status", meta={"kill_switch": {...}})
        """
        entry: Dict[str, Any] = {
            "ts": _utc_now_iso(),
            "run_id": self.run_id,
            "type": event_type,
            "level": level,
            "meta": dict(meta) if meta else {},
        }
        if fields:
            entry.update(fields)

        self._append(entry)

    def error(
        self,
        event_type: str,
        *,
        meta: Optional[Mapping[str, Any]] = None,
        **fields: Any,
    ) -> None:
        self.event(event_type, meta=meta, level="ERROR", **fields)

    # ---------------------------------------------------------------------
    # Backward compatible API (older code paths)
    # ---------------------------------------------------------------------
    def write(self, record_type: str, payload: Mapping[str, Any]) -> None:
        """
        Back-compat: older code wrote {type,data}.
        We map it to event(meta=payload).
        """
        self.event(record_type, meta=dict(payload))

    def write_many(self, record_type: str, items: Iterable[Mapping[str, Any]]) -> None:
        for item in items:
            self.write(record_type, item)
