# ats/backtester2/bt_debug_snapshot.py

from __future__ import annotations

from typing import Any, Dict


class SnapshotRecorder:
    """Records deep-dive snapshots of pipeline state for forensic debugging."""

    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.snapshots: Dict[int, Dict[str, Any]] = {}

    def record(self, ts: int, label: str, data: Dict[str, Any]):
        if not self.enabled:
            return

        if ts not in self.snapshots:
            self.snapshots[ts] = {}

        # shallow copy is fine — upstream structures are immutable at snapshot points
        self.snapshots[ts][label] = dict(data)

    def get(self, ts: int) -> Dict[str, Any] | None:
        return self.snapshots.get(ts)

    def dump_all(self) -> Dict[int, Dict[str, Any]]:
        return self.snapshots
