from typing import Any, Dict, List

import numpy as np


class PortfolioAnalytics:
    """Computes high-level portfolio statistics from equity curve samples."""

    @staticmethod
    def compute(equity_curve: List[Dict[str, Any]]) -> Dict[str, float]:
        if not equity_curve:
            return {}

        eq = np.array([row["equity"] for row in equity_curve])
        rets = np.diff(eq) / eq[:-1]

        if len(rets) == 0:
            return {}

        sharpe = (
            (np.mean(rets) / np.std(rets)) * np.sqrt(252) if np.std(rets) > 0 else 0
        )
        sortino = (
            (np.mean(rets) / np.std(rets[rets < 0])) * np.sqrt(252)
            if np.any(rets < 0)
            else 0
        )

        drawdown = eq - np.maximum.accumulate(eq)
        max_dd = abs(drawdown.min())
        volatility = np.std(rets) * np.sqrt(252)

        return {
            "sharpe": float(sharpe),
            "sortino": float(sortino),
            "max_drawdown": float(max_dd),
            "volatility": float(volatility),
            "return": float(eq[-1] / eq[0] - 1),
        }
