from typing import Any, Callable, Protocol


class EventBusInterface(Protocol):
    def publish(self, channel: str, payload: Any) -> None: ...

    def subscribe(self, channel: str, callback: Callable[[Any], None]) -> None: ...
