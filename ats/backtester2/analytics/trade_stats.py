import math
from typing import Any, Dict, List


class TradeStats:
    """Aggregates trade-level performance into summary statistics.

    Returns:
        {
            "total_trades": int,
            "win_rate": float,
            "avg_win": float,
            "avg_loss": float,
            "expectancy": float,
            "profit_factor": float,
            "best_trade": float,
            "worst_trade": float,
            "avg_mfe": float,
            "avg_mae": float,
        }

    """

    @staticmethod
    def compute(trades: List[Dict[str, Any]]) -> Dict[str, float]:
        if not trades:
            return {}

        pnls = [t["pnl"] for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]

        total = len(pnls)
        win_rate = len(wins) / total if total > 0 else 0.0
        avg_win = sum(wins) / len(wins) if wins else 0.0
        avg_loss = sum(losses) / len(losses) if losses else 0.0
        expectancy = win_rate * avg_win + (1 - win_rate) * avg_loss

        profit_factor = (sum(wins) / abs(sum(losses))) if losses else math.inf

        avg_mfe = sum(t["mfe"] for t in trades) / total
        avg_mae = sum(t["mae"] for t in trades) / total

        return {
            "total_trades": total,
            "win_rate": win_rate,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "expectancy": expectancy,
            "profit_factor": profit_factor,
            "best_trade": max(pnls),
            "worst_trade": min(pnls),
            "avg_mfe": avg_mfe,
            "avg_mae": avg_mae,
        }
