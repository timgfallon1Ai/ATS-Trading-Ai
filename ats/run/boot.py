from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ats.orchestrator.log_writer import LogWriter
from ats.run.orchestrator import Orchestrator
from ats.run.service_registry import ServiceRegistry
from ats.run.system_clock import SystemClock


@dataclass(frozen=True)
class BootConfig:
    """Boot configuration for the ats.run runtime."""

    log_dir: str = "logs"
    clock_interval_s: float = 1.0
    run_id: Optional[str] = None


def boot_system(config: Optional[BootConfig] = None) -> ServiceRegistry:
    """Create a ServiceRegistry with a logger + clock + orchestrator.

    The runtime is intentionally lightweight. For now we mostly use it to:
      - Provide a single entrypoint (python -m ats.run ...)
      - Wrap backtester2 runs with structured JSONL logs

    Live/paper mode services can be registered later without changing
    the orchestrator contract.
    """

    cfg = config or BootConfig()
    reg = ServiceRegistry()
    reg.add("log", LogWriter(log_dir=cfg.log_dir))
    reg.add("clock", SystemClock(interval=cfg.clock_interval_s))
    reg.add("orchestrator", Orchestrator(registry=reg, run_id=cfg.run_id))
    return reg
