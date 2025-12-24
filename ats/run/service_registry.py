from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable


@dataclass
class ServiceRegistry:
    """Tiny dependency-injection container.

    Keep it minimal, but make wiring failures obvious and debuggable.
    """

    services: Dict[str, Any] = field(default_factory=dict)

    def add(self, name: str, service: Any) -> None:
        if not name:
            raise ValueError("Service name cannot be empty")
        self.services[name] = service

    def get(self, name: str, default: Any | None = None) -> Any:
        return self.services.get(name, default)

    def __getitem__(self, name: str) -> Any:
        try:
            return self.services[name]
        except KeyError as e:
            available = ", ".join(sorted(self.services.keys()))
            raise KeyError(
                f"Service '{name}' not registered. Available: [{available}]"
            ) from e

    def __contains__(self, name: str) -> bool:
        return name in self.services

    def keys(self) -> Iterable[str]:
        return self.services.keys()

    def describe(self) -> Dict[str, str]:
        """Lightweight description of registered services."""
        return {k: type(v).__name__ for k, v in self.services.items()}
