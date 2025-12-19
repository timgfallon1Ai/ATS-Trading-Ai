from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class ServiceRegistry:
    """Simple dependency injection container for runtime services.

    This is intentionally small and boring. The goal is to have a single place
    to register/retrieve subsystem instances for the orchestrator/runtime.
    """

    services: Dict[str, Any] = field(default_factory=dict)

    def add(self, name: str, service: Any) -> None:
        self.services[name] = service

    def get(self, name: str, default: Any = None) -> Any:
        return self.services.get(name, default)

    def __getitem__(self, name: str) -> Any:
        return self.services[name]

    def __contains__(self, name: str) -> bool:
        return name in self.services
