from __future__ import annotations

from dataclasses import dataclass

from ats.orchestrator.log_writer import LogWriter
from ats.run.orchestrator import RuntimeOrchestrator
from ats.run.service_registry import ServiceRegistry


@dataclass(frozen=True)
class BootConfig:
    """Configuration for `boot_system`."""

    log_dir: str = "logs"
    run_id: str | None = None


def boot_system(cfg: BootConfig) -> ServiceRegistry:
    """Boot the minimal runtime service graph.

    Services guaranteed:
    - log: LogWriter
    - orchestrator: RuntimeOrchestrator
    - run_id: str
    """
    reg = ServiceRegistry()

    log = LogWriter(log_dir=cfg.log_dir, run_id=cfg.run_id)
    reg.add("log", log)
    reg.add("run_id", log.run_id)

    # IMPORTANT: ats.run.__main__ expects this key.
    reg.add("orchestrator", RuntimeOrchestrator(log=log))

    return reg
