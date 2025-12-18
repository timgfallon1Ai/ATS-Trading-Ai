from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping, Tuple


@dataclass(frozen=True)
class ExposureSnapshot:
    """Lightweight telemetry describing a weight vector."""

    gross: float
    net: float
    max_abs_symbol: float
    n_symbols: int


class ExposureRules:
    """RM-3 Exposure Rules.

    Operates on *signed weights* (e.g. +0.10 means long 10% notional,
    -0.10 means short 10% notional).

    These rules are intentionally conservative and deterministic:
    - Optional short disabling
    - Optional min abs weight cutoff (drops micro-positions)
    - Per-symbol absolute cap
    - Portfolio gross exposure cap (sum(abs(w)))
    - Portfolio net exposure cap (abs(sum(w))) for long/short neutrality control
    """

    def __init__(
        self,
        *,
        allow_short: bool = True,
        max_symbol_weight: float = 0.25,
        max_gross_leverage: float = 2.0,
        max_net_leverage: float = 1.0,
        min_abs_weight: float = 0.0,
    ) -> None:
        if max_symbol_weight <= 0.0:
            raise ValueError("max_symbol_weight must be > 0")
        if max_gross_leverage <= 0.0:
            raise ValueError("max_gross_leverage must be > 0")
        if max_net_leverage <= 0.0:
            raise ValueError("max_net_leverage must be > 0")
        if min_abs_weight < 0.0:
            raise ValueError("min_abs_weight must be >= 0")

        self.allow_short = allow_short
        self.max_symbol_weight = float(max_symbol_weight)
        self.max_gross_leverage = float(max_gross_leverage)
        self.max_net_leverage = float(max_net_leverage)
        self.min_abs_weight = float(min_abs_weight)

    @staticmethod
    def snapshot(weights: Mapping[str, float]) -> ExposureSnapshot:
        values = list(weights.values())
        gross = sum(abs(v) for v in values)
        net = abs(sum(values))
        max_abs_symbol = max((abs(v) for v in values), default=0.0)
        return ExposureSnapshot(
            gross=float(gross),
            net=float(net),
            max_abs_symbol=float(max_abs_symbol),
            n_symbols=len(values),
        )

    def apply(self, weights: Mapping[str, float]) -> Dict[str, float]:
        """Apply exposure constraints and return a new weights dict."""
        w: Dict[str, float] = {str(k): float(v) for k, v in weights.items()}

        # 1) Optional: disable shorts entirely.
        if not self.allow_short:
            for sym, val in list(w.items()):
                if val < 0.0:
                    w[sym] = 0.0

        # 2) Drop micro positions (helps both backtest and live).
        if self.min_abs_weight > 0.0:
            w = {sym: val for sym, val in w.items() if abs(val) >= self.min_abs_weight}

        # 3) Per-symbol cap.
        cap = self.max_symbol_weight
        for sym, val in list(w.items()):
            if abs(val) > cap:
                w[sym] = cap if val > 0.0 else -cap

        # 4) Gross exposure cap.
        gross = sum(abs(v) for v in w.values())
        if gross > self.max_gross_leverage and gross > 0.0:
            scale = self.max_gross_leverage / gross
            for sym in list(w.keys()):
                w[sym] *= scale

        # 5) Net exposure cap (helps prevent one-sided books if you want neutrality).
        net = abs(sum(w.values()))
        if net > self.max_net_leverage and net > 0.0:
            scale = self.max_net_leverage / net
            for sym in list(w.keys()):
                w[sym] *= scale

        # 6) Drop exact zeros for cleanliness.
        return {sym: val for sym, val in w.items() if val != 0.0}

    def apply_with_snapshot(
        self, weights: Mapping[str, float]
    ) -> Tuple[Dict[str, float], ExposureSnapshot]:
        adjusted = self.apply(weights)
        return adjusted, self.snapshot(adjusted)
