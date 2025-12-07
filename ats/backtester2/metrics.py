# ats/backtester2/metrics.py

from __future__ import annotations

from typing import Dict, List


class MetricsEngine:
    """Computes all performance + risk metrics from a time-ordered list of
    equity snapshots.

    All inputs are raw Python floats and lists, no Pandas/NumPy required.

    Public API:
        - update(equity: float)
        - finalize() -> Dict[str, float]
        - curve -> List[float]
        - drawdowns -> List[float]
    """

    def __init__(self):
        self.curve: List[float] = []  # equity curve
        self.drawdowns: List[float] = []  # drawdown curve
        self.returns: List[float] = []  # per-step returns

    # ----------------------------------------------------
    # UPDATE ON EACH BAR
    # ----------------------------------------------------
    def update(self, equity: float):
        """Called after each bar to append new equity value and compute per-bar stats."""
        self.curve.append(equity)

        # Compute returns
        if len(self.curve) > 1:
            prev = self.curve[-2]
            if prev > 0:
                self.returns.append((equity - prev) / prev)
            else:
                self.returns.append(0.0)

        # Compute drawdowns
        peak = max(self.curve)
        dd = (equity - peak) / peak if peak > 0 else 0.0
        self.drawdowns.append(dd)

    # ----------------------------------------------------
    # METRIC COMPUTATIONS
    # ----------------------------------------------------
    def compute_total_return(self) -> float:
        if not self.curve:
            return 0.0
        start = self.curve[0]
        end = self.curve[-1]
        if start <= 0:
            return 0.0
        return (end / start) - 1.0

    def compute_max_drawdown(self) -> float:
        if not self.drawdowns:
            return 0.0
        return min(self.drawdowns)

    def compute_sharpe(self) -> float:
        """Simple Sharpe (no risk-free rate)."""
        if not self.returns:
            return 0.0
        mean = sum(self.returns) / len(self.returns)
        var = sum((r - mean) ** 2 for r in self.returns) / len(self.returns)
        std = var**0.5
        if std == 0:
            return 0.0
        return mean / std

    def compute_sortino(self) -> float:
        """Downside-only risk."""
        if not self.returns:
            return 0.0

        downside = [r for r in self.returns if r < 0]
        if not downside:
            return 0.0

        mean = sum(self.returns) / len(self.returns)
        var = sum((r - 0.0) ** 2 for r in downside) / len(downside)
        std = var**0.5

        if std == 0:
            return 0.0
        return mean / std

    def compute_volatility(self) -> float:
        if not self.returns:
            return 0.0
        mean = sum(self.returns) / len(self.returns)
        var = sum((r - mean) ** 2 for r in self.returns) / len(self.returns)
        return var**0.5

    # ----------------------------------------------------
    # FINAL METRIC SNAPSHOT
    # ----------------------------------------------------
    def finalize(self) -> Dict[str, float]:
        return {
            "total_return": self.compute_total_return(),
            "max_drawdown": self.compute_max_drawdown(),
            "sharpe": self.compute_sharpe(),
            "sortino": self.compute_sortino(),
            "volatility": self.compute_volatility(),
            "final_equity": self.curve[-1] if self.curve else 0.0,
            "start_equity": self.curve[0] if self.curve else 0.0,
            "curve_length": len(self.curve),
        }
