import time


class SystemClock:
    """Master heartbeat for live trading and simulated environments."""

    def __init__(self, interval: float = 1.0):
        self.interval = interval

    def wait(self):
        time.sleep(self.interval)
