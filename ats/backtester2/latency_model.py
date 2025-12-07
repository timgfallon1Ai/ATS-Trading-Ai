# ats/backtester2/latency_model.py

from __future__ import annotations

import random


class LatencyModel:
    """Deterministic or bounded-random latency model."""

    def __init__(
        self, mean_ms: int = 20, jitter_ms: int = 5, deterministic: bool = True
    ):
        self.mean_ms = mean_ms
        self.jitter_ms = jitter_ms
        self.deterministic = deterministic

    def delay_milliseconds(self) -> int:
        if self.deterministic:
            return self.mean_ms
        return max(0, int(random.gauss(self.mean_ms, self.jitter_ms)))
