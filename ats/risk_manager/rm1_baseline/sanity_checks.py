import math
from datetime import datetime, timezone
from typing import Any, Dict


class SanityChecks:
    """RM-1 Sanity checks: ensures incoming allocations, signals, and volatility
    are safe to process before deeper risk engines execute.
    """

    @staticmethod
    def is_valid_number(x: Any) -> bool:
        try:
            return (
                x is not None and not math.isnan(float(x)) and not math.isinf(float(x))
            )
        except Exception:
            return False

    def validate_signal(self, sig: Dict) -> bool:
        required = ["symbol", "score", "confidence", "strategy"]

        for field in required:
            if field not in sig:
                return False

        if not self.is_valid_number(sig.get("score")):
            return False

        if not self.is_valid_number(sig.get("confidence")):
            return False

        if not isinstance(sig.get("symbol"), str) or len(sig["symbol"]) == 0:
            return False

        return True

    def validate_volatility(self, vol: float) -> bool:
        if not self.is_valid_number(vol):
            return False
        if vol <= 0:
            return False
        if vol > 5:  # insane volatility values
            return False
        return True

    def validate_timestamp(self, ts: str, max_age_seconds: int = 10) -> bool:
        # Accepts ISO timestamps from AnalystEngine
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            return False

        now = datetime.now(timezone.utc)
        age = (now - dt).total_seconds()

        return age <= max_age_seconds

    def validate_allocation(self, alloc: Dict) -> bool:
        """Validates output from Aggregator: qty, symbol, strategy_breakdown, timestamp."""
        if "symbol" not in alloc or not isinstance(alloc["symbol"], str):
            return False

        if "qty" not in alloc or not self.is_valid_number(alloc["qty"]):
            return False

        if alloc["qty"] < 0:
            return False

        if "strategy_breakdown" not in alloc or not isinstance(
            alloc["strategy_breakdown"], dict
        ):
            return False

        if "timestamp" not in alloc or not self.validate_timestamp(alloc["timestamp"]):
            return False

        return True
