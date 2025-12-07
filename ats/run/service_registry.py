from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ServiceRegistry:
    """Central dependency injection container.
    Holds handles to every subsystem in the ATS.
    """

    services: Dict[str, Any]

    def add(self, name: str, service: Any) -> None:
        self.services[name] = service

    def get(self, name: str) -> Any:
        return self.services[name]

    def __getitem__(self, name: str) -> Any:
        return self.services[name]
