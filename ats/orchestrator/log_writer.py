"""
Structured JSONL logger for ATS.

Writes:
  <base_log_dir>/<run_id>/events.jsonl

Each line is a single JSON object. This logger must never crash the runtime
due to non-JSON-native types (e.g., pathlib.Path, datetime, UUID, exceptions).
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional


def _utc_now_iso() -> str:
    # Example: 2025-12-21T21:37:34.123456Z
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _json_default(obj: Any) -> Any:
    """
    json.dumps(default=...) hook.

    Converts common non-serializable objects into safe JSON representations.
    """
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, datetime):
        # Ensure timezone-safe output if tz-aware
        try:
            return obj.astimezone(timezone.utc).isoformat()
        except Exception:
            return obj.isoformat()
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if is_dataclass(obj):
        try:
            return asdict(obj)
        except Exception:
            return str(obj)
    if isinstance(obj, BaseException):
        return {
            "type": obj.__class__.__name__,
            "message": str(obj),
        }

    # Last resort: stringify unknown objects rather than failing the run
    return str(obj)


class LogWriter:
    """
    Append-only JSONL event logger.

    Public API used by ats.run:
      - event(name, meta=..., **fields)
    """

    def __init__(self, log_dir: str | Path = "logs", run_id: Optional[str] = None):
        base = Path(log_dir)
        rid = run_id or self._generate_run_id()

        self.base_dir: Path = base
        self.run_id: str = str(rid)
        self.log_dir: Path = self.base_dir / self.run_id
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.events_path: Path = self.log_dir / "events.jsonl"

    @staticmethod
    def _generate_run_id() -> str:
        # Keep consistent with prior runs: <UTCSTAMP>-<8hex>
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return f"{stamp}-{uuid.uuid4().hex[:8]}"

    def _append(self, entry: Mapping[str, Any]) -> None:
        # Ensure directory exists even if external cleanup happens mid-run.
        self.log_dir.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    dict(entry),
                    ensure_ascii=False,
                    default=_json_default,
                )
                + "\n"
            )

    def event(self, name: str, meta: Any = None, **fields: Any) -> Dict[str, Any]:
        """
        Write an event line.

        - name: event name
        - meta: any metadata payload (dict recommended, but can be any object)
        - fields: extra top-level fields (level, msg, counts, etc)
        """
        entry: Dict[str, Any] = {
            "ts": _utc_now_iso(),
            "run_id": self.run_id,
            "event": str(name),
        }

        if meta is not None:
            entry["meta"] = meta

        # allow caller to add top-level fields (level, msg, durations, etc)
        for k, v in fields.items():
            entry[str(k)] = v

        self._append(entry)
        return entry

    @property
    def path(self) -> Path:
        # Convenience alias used by some call sites
        return self.events_path
