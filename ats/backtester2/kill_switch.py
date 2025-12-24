from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Optional


def _kill_switch_path() -> Path:
    """Return the filesystem path used to signal a kill switch.

    The path can be overridden with ATS_KILL_SWITCH_FILE.
    """

    env = os.getenv("ATS_KILL_SWITCH_FILE")
    if env:
        return Path(env).expanduser()

    # Use a deterministic default path that works on macOS/Linux.
    return Path("/tmp/ats_kill_switch.json")


def enable_kill_switch(reason: str = "manual kill switch") -> None:
    """Enable the kill switch by writing a small JSON file.

    Any running backtest loop should periodically check kill_switch_engaged()
    and halt safely if enabled.
    """
    p = _kill_switch_path()
    p.parent.mkdir(parents=True, exist_ok=True)

    payload = {"enabled": True, "ts": time.time(), "reason": reason}
    p.write_text(json.dumps(payload), encoding="utf-8")


def disable_kill_switch() -> None:
    """Disable the kill switch by removing the file (if present)."""
    p = _kill_switch_path()
    try:
        p.unlink()
    except FileNotFoundError:
        return


def kill_switch_engaged() -> bool:
    """Return True if the kill switch file exists and is enabled."""
    p = _kill_switch_path()
    if not p.exists():
        return False

    try:
        data = json.loads(p.read_text(encoding="utf-8") or "{}")
    except Exception:
        # If file is corrupted, fail safe: treat as engaged.
        return True

    return bool(data.get("enabled", True))


def read_kill_switch_reason() -> Optional[str]:
    """Return the reason string if the kill switch is engaged (if available)."""
    p = _kill_switch_path()
    if not p.exists():
        return None

    try:
        data = json.loads(p.read_text(encoding="utf-8") or "{}")
        return data.get("reason")
    except Exception:
        return None
