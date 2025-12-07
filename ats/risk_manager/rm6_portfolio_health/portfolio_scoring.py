from typing import Dict

from .portfolio_state import PortfolioState
from .strategy_reputation import StrategyReputation


class PortfolioScoring:
    """Computes final RM-6 portfolio health score.

    Combines:
    - drawdown profile
    - volatility stability
    - strategy reputation
    - capital efficiency
    """

    def __init__(self):
        self.reputation = StrategyReputation()

    def score(self, state: PortfolioState, pnl: float, alloc: Dict[str, float]) -> Dict:
        """pnl: total PnL since last update
        alloc: any structure containing strategy_breakdown
        """
        # Update reputation based on which strategies caused pnl
        self.reputation.update(alloc.get("strategy_breakdown", {}), pnl)

        # Drawdown score (higher DD -> lower health)
        dd = state.drawdowns[-1] if state.drawdowns else 0
        drawdown_score = max(0.0, 1.0 + dd)  # dd is negative when in drawdown

        # Volatility stability
        vol = state.vols[-1] if state.vols else 0
        vol_stability = max(0.0, min(1.0, 1.0 - (vol * 5)))

        # Capital efficiency: profit relative to volatility
        eff = (pnl / (vol + 1e-6)) if vol > 0 else pnl
        efficiency_score = max(0.0, min(1.0, eff * 0.1 + 0.5))

        # Strategy reputation
        rep = self.reputation.get()
        rep_avg = sum(rep.values()) / len(rep) if rep else 0.5

        # Final portfolio health score
        portfolio_health = (
            drawdown_score * 0.3
            + vol_stability * 0.3
            + efficiency_score * 0.2
            + rep_avg * 0.2
        )

        return {
            "portfolio_health": float(max(0.0, min(1.0, portfolio_health))),
            "drawdown": float(dd),
            "volatility_stability": float(vol_stability),
            "capital_efficiency": float(efficiency_score),
            "strategy_reputation": rep.copy(),
        }
