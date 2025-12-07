import math
from dataclasses import dataclass, field
from typing import List


@dataclass
class PortfolioState:
    """Tracks portfolio-level time series for RM-6 scoring.
    Second-level abstraction above Trader positions.
    """

    equity_curve: List[float] = field(default_factory=list)
    returns: List[float] = field(default_factory=list)
    drawdowns: List[float] = field(default_factory=list)
    vols: List[float] = field(default_factory=list)

    def update(self, portfolio_value: float):
        if not self.equity_curve:
            self.equity_curve.append(portfolio_value)
            self.returns.append(0.0)
            self.drawdowns.append(0.0)
            self.vols.append(0.0)
            return

        prev = self.equity_curve[-1]
        ret = (portfolio_value - prev) / max(prev, 1e-9)

        self.equity_curve.append(portfolio_value)
        self.returns.append(ret)

        # Rolling volatility (last 20 samples)
        window = self.returns[-20:]
        vol = (
            math.sqrt(sum(r * r for r in window) / len(window))
            if len(window) > 1
            else 0.0
        )
        self.vols.append(vol)

        # Drawdown
        peak = max(self.equity_curve)
        dd = (portfolio_value - peak) / peak
        self.drawdowns.append(dd)
