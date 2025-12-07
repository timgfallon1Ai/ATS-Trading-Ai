from typing import Optional

from .in_memory_bus import InMemoryBus
from .interfaces import EventBusInterface
from .redis_bus import RedisBus


class EventBusFactory:
    _bus: Optional[EventBusInterface] = None

    @classmethod
    def get(cls) -> EventBusInterface:
        if cls._bus is None:
            cls._bus = InMemoryBus()
        return cls._bus

    @classmethod
    def use_memory(cls) -> None:
        cls._bus = InMemoryBus()

    @classmethod
    def use_redis(cls, url: str) -> None:
        cls._bus = RedisBus(url)
