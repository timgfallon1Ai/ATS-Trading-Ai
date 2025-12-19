from __future__ import annotations

import time


class SystemClock:
    """Master heartbeat for live trading and simulated environments."""

    def __init__(self, interval: float = 1.0):
        self.interval = float(interval)

    def wait(self) -> None:
        time.sleep(self.interval)
