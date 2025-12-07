from __future__ import annotations

from typing import Any, Callable, Dict


class LiveOrderRouter:
    """Allows swapping between:
    - Simulated execution
    - Live exchange API execution
    """

    def __init__(self, route_fn: Callable[[Dict[str, Any]], Any]):
        self.route_fn = route_fn

    def send(self, order: Dict[str, Any]) -> Any:
        return self.route_fn(order)
