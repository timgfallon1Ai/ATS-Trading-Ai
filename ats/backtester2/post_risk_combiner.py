# ats/backtester2/post_risk_combiner.py

from __future__ import annotations

from typing import Dict


class PostRiskCombiner:
    """Final signal-cleaning stage before position sizing.

    Responsibilities:
    -----------------
    - Remove extremely small signals (debounce)
    - Clip any oversized signals (e.g., > 1.0 or < -1.0)
    - Optional normalization across the symbol universe

    Output Contract:
    ----------------
    BT-2A expects:
        { symbol: clean_signal(float) }
    """

    def __init__(
        self,
        min_abs_signal: float = 0.05,
        max_abs_signal: float = 1.0,
        normalize: bool = True,
    ):
        self.min_abs_signal = min_abs_signal
        self.max_abs_signal = max_abs_signal
        self.normalize = normalize

    # ------------------------------------------------------------------
    # Main API
    # ------------------------------------------------------------------
    def combine(self, signals: Dict[str, float]) -> Dict[str, float]:
        """Input:
            raw_post_risk_signals = { symbol: float }
        Output:
            cleaned_signals = { symbol: float }
        """
        # 1) Remove micro-noise
        cleaned = {s: v for s, v in signals.items() if abs(v) >= self.min_abs_signal}

        if not cleaned:
            return {}

        # 2) Clip excessively strong signals
        for s in cleaned:
            if cleaned[s] > self.max_abs_signal:
                cleaned[s] = self.max_abs_signal
            elif cleaned[s] < -self.max_abs_signal:
                cleaned[s] = -self.max_abs_signal

        # 3) Optional normalization (L1)
        if self.normalize:
            total = sum(abs(v) for v in cleaned.values())
            if total > 0:
                cleaned = {s: v / total for s, v in cleaned.items()}

        return cleaned
