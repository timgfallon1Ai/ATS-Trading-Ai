from __future__ import annotations

import json
import os
import socket
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Union


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _safe_dir(path: Path) -> Path:
    """Ensure *path* is a directory.

    If *path* exists as a FILE, we cannot mkdir() it. In that case, fall back to a
    sibling directory (e.g. "logs_dir"). This prevents hard crashes like:
    FileExistsError: [Errno 17] File exists: 'logs'
    """
    if str(path).strip() == "":
        path = Path("logs")

    if path.exists() and path.is_file():
        # Common culprit: a tracked file named `logs` at repo root.
        candidate = path.with_name(f"{path.name}_dir")
        if candidate.exists() and candidate.is_file():
            candidate = path.with_name(f"{path.name}_dir_{uuid.uuid4().hex[:8]}")
        path = candidate

    path.mkdir(parents=True, exist_ok=True)
    return path


class LogWriter:
    """Unified ATS logging layer.

    - Writes JSONL logs for governance events, risk packets, and trade/fill results.
    - Scopes logs by run_id so multiple runs don't collide.
    - Robust to a common local-repo mistake: having a FILE named `logs`.
    """

    def __init__(
        self,
        log_dir: Union[str, Path] = "logs",
        run_id: Optional[str] = None,
    ) -> None:
        base = Path(log_dir)
        self.base_dir = _safe_dir(base)

        self.run_id = run_id or os.environ.get("ATS_RUN_ID") or self._new_run_id()
        self.run_dir = _safe_dir(self.base_dir / self.run_id)

        # Backwards-compat attribute: some code may read `log_writer.log_dir`
        self.log_dir = self.run_dir

        self._host = socket.gethostname()
        self._pid = os.getpid()

    def _new_run_id(self) -> str:
        ts = _utc_now().strftime("%Y%m%dT%H%M%SZ")
        return f"{ts}-{uuid.uuid4().hex[:8]}"

    def _file(self) -> Path:
        """Daily log file (within the run-scoped directory)."""
        date = _utc_now().strftime("%Y-%m-%d")
        return self.run_dir / f"{date}.jsonl"

    def write(self, record_type: str, payload: Dict[str, Any]) -> None:
        """Write a single JSONL record."""
        entry = {
            "ts": _utc_now().isoformat(),
            "run_id": self.run_id,
            "type": record_type,
            "data": payload,
            "meta": {"host": self._host, "pid": self._pid},
        }

        with self._file().open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    entry,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    default=str,
                )
                + "\n"
            )

    def write_many(self, record_type: str, items: Iterable[Dict[str, Any]]) -> None:
        for item in items:
            self.write(record_type, item)

    def session_start(self, payload: Optional[Dict[str, Any]] = None) -> None:
        self.write("session_start", payload or {})

    def session_end(self, payload: Optional[Dict[str, Any]] = None) -> None:
        self.write("session_end", payload or {})

    def session_error(
        self, exc: BaseException, payload: Optional[Dict[str, Any]] = None
    ) -> None:
        data = dict(payload or {})
        data["error"] = repr(exc)
        data["traceback"] = traceback.format_exc()
        self.write("session_error", data)
