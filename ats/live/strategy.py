from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List

from ats.live.broker import Broker
from ats.live.types import Bar
from ats.trader.order import Order


class LiveStrategy(ABC):
    name: str

    @abstractmethod
    def on_tick(self, bars: Dict[str, Bar], broker: Broker) -> List[Order]:
        raise NotImplementedError
