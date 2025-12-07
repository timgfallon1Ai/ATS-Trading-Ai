from __future__ import annotations

import random
import time
from typing import Any, Dict


class LatencyModel:
    """Adds a realistic exchange latency delay."""

    def __init__(self, base_ms: float = 25.0):
        self.base = base_ms / 1000.0

    def apply(self, order: Dict[str, Any]) -> Dict[str, Any]:
        delay = self.base * (0.8 + 0.4 * random.random())
        time.sleep(delay)
        return order
