from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ats.orchestrator.log_writer import LogWriter
from ats.run.service_registry import ServiceRegistry


@dataclass(frozen=True)
class BootConfig:
    log_dir: str = "logs"
    run_id: Optional[str] = None


def boot_system(cfg: BootConfig) -> ServiceRegistry:
    """Boot the minimal dependency registry for the unified runtime.

    Backtest-first: keep this light and deterministic.
    """
    reg = ServiceRegistry(services={})

    reg.add("boot_config", cfg)
    reg.add("log", LogWriter(log_dir=cfg.log_dir, run_id=cfg.run_id))

    return reg
