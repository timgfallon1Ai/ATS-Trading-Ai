from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union

DEFAULT_KILL_FILE = "logs/KILL_SWITCH"

ENV_KILL_FILE = "ATS_KILL_SWITCH_FILE"
ENV_FORCE_KILL = "ATS_KILL_SWITCH"
ENV_IGNORE_KILL = "ATS_IGNORE_KILL_SWITCH"


def _truthy(val: Optional[str]) -> bool:
    return (val or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _safe_path(p: Path) -> Path:
    """
    If the parent exists as a FILE (common repo artifact mistake), fall back to *_dir.
    Example: 'logs' is a file => write kill file under 'logs_dir/' instead.
    """
    parent = p.parent
    if parent.exists() and parent.is_file():
        parent = parent.with_name(parent.name + "_dir")
        return parent / p.name
    return p


def kill_switch_path(override: Optional[Union[str, Path]] = None) -> Path:
    raw = override or os.environ.get(ENV_KILL_FILE) or DEFAULT_KILL_FILE
    p = Path(str(raw)).expanduser()
    return _safe_path(p)


@dataclass(frozen=True)
class KillSwitchStatus:
    engaged: bool
    forced_by_env: bool
    ignored_by_env: bool
    file_exists: bool
    path: Path
    enabled_at: Optional[str]
    reason: Optional[str]


def read_kill_switch_status(
    override: Optional[Union[str, Path]] = None,
) -> KillSwitchStatus:
    ignored = _truthy(os.environ.get(ENV_IGNORE_KILL))
    forced = _truthy(os.environ.get(ENV_FORCE_KILL))
    path = kill_switch_path(override)

    file_exists = path.exists()
    enabled_at: Optional[str] = None
    reason: Optional[str] = None

    if file_exists:
        try:
            text = path.read_text(encoding="utf-8", errors="replace").strip()
            # Expected format (one line):
            # enabled_at=<iso> reason=<text>
            if text:
                parts = text.split("reason=", 1)
                left = parts[0].strip()
                if left.startswith("enabled_at="):
                    enabled_at = left.split("enabled_at=", 1)[1].strip()
                if len(parts) == 2:
                    reason = parts[1].strip() or None
        except Exception:
            enabled_at = None
            reason = None

    engaged = (not ignored) and (forced or file_exists)

    return KillSwitchStatus(
        engaged=engaged,
        forced_by_env=forced,
        ignored_by_env=ignored,
        file_exists=file_exists,
        path=path,
        enabled_at=enabled_at,
        reason=reason,
    )


def kill_switch_engaged(override: Optional[Union[str, Path]] = None) -> bool:
    return read_kill_switch_status(override).engaged


def enable_kill_switch(
    reason: str = "manual",
    override: Optional[Union[str, Path]] = None,
) -> Path:
    path = kill_switch_path(override)
    path.parent.mkdir(parents=True, exist_ok=True)

    enabled_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    payload = f"enabled_at={enabled_at} reason={reason}".strip() + "\n"
    path.write_text(payload, encoding="utf-8")
    return path


def disable_kill_switch(override: Optional[Union[str, Path]] = None) -> None:
    path = kill_switch_path(override)
    try:
        if path.exists():
            path.unlink()
    except Exception:
        # Do not raise; disable should be best-effort.
        pass
