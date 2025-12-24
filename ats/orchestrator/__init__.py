"""
ats.orchestrator (package)

This repo previously had a name collision:
- ats/orchestrator.py            (module file)
- ats/orchestrator/              (directory containing log_writer.py)

That collision breaks imports like:
    from ats.orchestrator.log_writer import LogWriter

because Python can resolve `ats.orchestrator` to the module file, not the directory.

This package initializer is intentionally LIGHTWEIGHT to avoid circular imports.
We provide a small amount of compatibility via lazy attribute access (PEP 562):
- LogWriter      -> ats.orchestrator.log_writer.LogWriter
- BootConfig     -> ats.run.boot.BootConfig
- boot_system    -> ats.run.boot.boot_system
- ATSOrchestrator (optional legacy) -> ats.orchestrator_facade.ATSOrchestrator (if present)

New code should prefer explicit imports:
    from ats.orchestrator.log_writer import LogWriter
    from ats.run.boot import BootConfig, boot_system
"""

from __future__ import annotations

from typing import Any

__all__ = ["LogWriter", "BootConfig", "boot_system", "ATSOrchestrator"]


def __getattr__(name: str) -> Any:
    if name == "LogWriter":
        from .log_writer import LogWriter

        return LogWriter

    if name in ("BootConfig", "boot_system"):
        # Keep this lazy to avoid circular imports during boot.
        from ats.run.boot import BootConfig, boot_system

        return BootConfig if name == "BootConfig" else boot_system

    if name == "ATSOrchestrator":
        # Optional backwards-compat path, if you still have a legacy orchestrator class.
        try:
            from ats.orchestrator_facade import ATSOrchestrator  # type: ignore

            return ATSOrchestrator
        except Exception as e:  # pragma: no cover
            raise AttributeError(
                "ATSOrchestrator is not available. "
                "If you still need it, ensure ats/orchestrator_facade.py defines ATSOrchestrator."
            ) from e

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
