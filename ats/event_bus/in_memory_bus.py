from typing import Any, Callable, Dict, List

from .interfaces import EventBusInterface


class InMemoryBus(EventBusInterface):
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Any], None]]] = {}

    def publish(self, channel: str, payload: Any) -> None:
        for callback in self._subscribers.get(channel, []):
            callback(payload)

    def subscribe(self, channel: str, callback: Callable[[Any], None]) -> None:
        self._subscribers.setdefault(channel, []).append(callback)
