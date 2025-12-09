"""RM-2 Predictive Risk Engine.

This module provides a lightweight predictive risk component that can be
plugged into the higher-level RiskManager.

It is intentionally conservative and self-contained for this phase:

- Maintains a rolling window of returns.
- Computes a simple realized volatility estimate.
- Derives a coarse "regime" classification (calm / stressed).
- Exposes a normalized risk score in [0.0, 1.0].

For now this is used primarily as a building block for future phases.
The important bit for compatibility is that we expose BOTH:

- PredictiveRiskEngine  (the primary class)
- PredictiveEngine      (a backward-compatible alias used by RiskManager)
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from statistics import mean
from typing import List, Optional


@dataclass
class PredictiveConfig:
    """Configuration for the predictive risk engine."""

    lookback: int = 50
    vol_threshold_calm: float = 0.01  # 1% daily vol ~ calm
    vol_threshold_stressed: float = 0.03  # 3%+ daily vol ~ stressed
    min_samples: int = 10


class PredictiveRiskEngine:
    """Simple, self-contained predictive risk component.

    This is intentionally modest in scope for now. It is designed so that
    we can replace the internals with something more sophisticated later
    (ML models, regime HMMs, etc.) without changing the interface that
    the rest of the system relies on.
    """

    def __init__(self, config: Optional[PredictiveConfig] = None) -> None:
        self.config = config or PredictiveConfig()
        self._returns: List[float] = []

    # ------------------------------------------------------------------
    # Data ingestion
    # ------------------------------------------------------------------
    def update_return(self, ret: float) -> None:
        """Feed a single-period return into the engine.

        Args:
            ret: Period return (e.g., daily return) as a decimal, not percent.
        """
        self._returns.append(ret)
        if len(self._returns) > self.config.lookback:
            self._returns.pop(0)

    # ------------------------------------------------------------------
    # Volatility & regime estimation
    # ------------------------------------------------------------------
    def _realized_vol(self) -> Optional[float]:
        """Compute a naive realized volatility over the rolling window."""
        if len(self._returns) < self.config.min_samples:
            return None

        mu = mean(self._returns)
        var = mean((r - mu) ** 2 for r in self._returns)
        return sqrt(var)

    def regime(self) -> str:
        """Return a coarse volatility regime label.

        Returns:
            "unknown"  if we don't have enough data yet
            "calm"     if realized vol is below the calm threshold
            "normal"   if between calm and stressed
            "stressed" if above the stressed threshold
        """
        vol = self._realized_vol()
        if vol is None:
            return "unknown"

        if vol < self.config.vol_threshold_calm:
            return "calm"
        if vol > self.config.vol_threshold_stressed:
            return "stressed"
        return "normal"

    # ------------------------------------------------------------------
    # Normalized risk score
    # ------------------------------------------------------------------
    def risk_score(self) -> float:
        """Return a normalized risk score in [0.0, 1.0].

        0.0   => extremely calm / no signal
        0.5   => normal / baseline
        1.0   => highly stressed
        """
        vol = self._realized_vol()
        if vol is None:
            # No view yet: treat as baseline
            return 0.5

        # Map vol into [0, 1] using the calm/stressed thresholds as key points.
        if vol <= self.config.vol_threshold_calm:
            return 0.0
        if vol >= self.config.vol_threshold_stressed:
            return 1.0

        span = self.config.vol_threshold_stressed - self.config.vol_threshold_calm
        if span <= 0:
            # Defensive: misconfigured thresholds, fall back to mid
            return 0.5

        return (vol - self.config.vol_threshold_calm) / span

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    def snapshot(self) -> dict:
        """Return a lightweight diagnostic snapshot for logging / dashboards."""
        vol = self._realized_vol()
        return {
            "samples": len(self._returns),
            "realized_vol": vol,
            "regime": self.regime(),
            "risk_score": self.risk_score(),
        }


class PredictiveEngine(PredictiveRiskEngine):
    """Backward-compatible alias.

    Legacy code in the risk manager imports `PredictiveEngine` from this
    module. To avoid breaking that code – and to give us freedom to evolve
    the implementation – we provide this subclass alias.
    """

    pass
