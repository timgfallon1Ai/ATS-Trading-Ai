from __future__ import annotations


class PostureSync:
    """Determines whether the system is in 'normal', 'cautious', or 'aggressive' mode.
    Uses the $1k → $2k transition rule you specified.
    """

    def __init__(self, initial_equity: float = 1000.0) -> None:
        self.initial_equity = initial_equity
        self.equity = initial_equity

    def update_equity(self, new_equity: float) -> None:
        self.equity = new_equity

    def posture(self) -> str:
        if self.equity >= self.initial_equity * 2:
            return "aggressive"
        if self.equity <= self.initial_equity * 0.85:
            return "cautious"
        return "normal"
