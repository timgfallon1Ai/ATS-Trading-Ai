from datetime import datetime, timezone
from typing import Any, Dict


class BaselineRules:
    """RM-1 Baseline Safety Rules.

    Hard, non-negotiable constraints that ensure:
    - No oversized trades
    - No invalid signals
    - No low-confidence trades
    - No trades in extreme conditions
    - No stale signals
    - Protects the $1K principal before higher-level RM logic runs
    """

    def __init__(
        self,
        max_position: float = 10_000,
        min_confidence: float = 0.10,
        max_score: float = 1.0,
        trading_start_hour: int = 8,
        trading_end_hour: int = 15,
    ):
        self.max_position = max_position
        self.min_confidence = min_confidence
        self.max_score = max_score
        self.trading_start_hour = trading_start_hour
        self.trading_end_hour = trading_end_hour

    def _within_trading_hours(self) -> bool:
        now = datetime.now(timezone.utc).astimezone()
        return self.trading_start_hour <= now.hour <= self.trading_end_hour

    def check_confidence(self, confidence: float) -> bool:
        return confidence >= self.min_confidence

    def check_score(self, score: float) -> bool:
        return 0 <= score <= self.max_score

    def check_position_size(self, qty: float) -> bool:
        return 0 <= qty <= self.max_position

    def check_timestamp_freshness(self, ts: str, max_age_seconds: int = 10) -> bool:
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            return False

        now = datetime.now(timezone.utc)
        return (now - dt).total_seconds() <= max_age_seconds

    def check_trading_window(self) -> bool:
        return self._within_trading_hours()

    def run(self, alloc: Dict[str, Any]) -> bool:
        """Returns True if allocation is SAFE to continue through RM-2 → RM-7."""
        if not self.check_confidence(alloc.get("confidence", 0)):
            return False

        if not self.check_score(alloc.get("combined_score", alloc.get("score", 0))):
            return False

        if not self.check_position_size(alloc.get("qty", 0)):
            return False

        if not self.check_timestamp_freshness(alloc.get("timestamp", "")):
            return False

        if not self.check_trading_window():
            return False

        return True
