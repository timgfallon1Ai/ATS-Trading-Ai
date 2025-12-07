import time


class Clock:
    """Uniform time abstraction for live + backtests."""

    @staticmethod
    def now_ms() -> int:
        return int(time.time() * 1000)
