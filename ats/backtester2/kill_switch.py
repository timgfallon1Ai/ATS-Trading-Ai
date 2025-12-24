cat > ats / backtester2 / kill_switch.py << "PY"
"""
Backtester2 kill-switch helpers.

Backtester2 tests import these helpers from `ats.backtester2.kill_switch`,
but the canonical implementation lives in `ats.core.kill_switch`.

This module is intentionally a thin re-export to keep a single source of truth.
"""

from ats.core.kill_switch import (  # noqa: F401
    KillSwitchStatus,
    disable_kill_switch,
    enable_kill_switch,
    kill_switch_engaged,
    read_kill_switch_status,
)

__all__ = [
    "KillSwitchStatus",
    "disable_kill_switch",
    "enable_kill_switch",
    "kill_switch_engaged",
    "read_kill_switch_status",
]
PY
