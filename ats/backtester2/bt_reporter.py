# ats/backtester2/bt_reporter.py

from __future__ import annotations

import math
from typing import Any, Dict, List


def _max_drawdown(values: List[float]) -> float:
    peak = values[0]
    max_dd = 0.0
    for v in values:
        peak = max(peak, v)
        dd = (peak - v) / peak if peak > 0 else 0.0
        max_dd = max(max_dd, dd)
    return max_dd


def _sharpe(returns: List[float]) -> float:
    if len(returns) < 2:
        return 0.0
    mean_ret = sum(returns) / len(returns)
    var = sum((r - mean_ret) ** 2 for r in returns) / (len(returns) - 1)
    std = math.sqrt(var) if var > 0 else 0.0
    return mean_ret / std if std > 0 else 0.0


def generate_report(
    equity_curve: List[float],
    pnl_series: List[float],
    trades: List[Dict[str, Any]],
    per_symbol_returns: Dict[str, float],
    exposure_series: List[float],
    turnover_series: List[float],
) -> Dict[str, Any]:

    returns = pnl_series
    dd = _max_drawdown(equity_curve)
    sharpe = _sharpe(returns)

    return {
        "equity_curve": equity_curve,
        "pnl": pnl_series,
        "drawdown": dd,
        "sharpe": sharpe,
        "trades": trades,
        "per_symbol_returns": per_symbol_returns,
        "exposure": exposure_series,
        "turnover": turnover_series,
        "summary": {
            "final_equity": equity_curve[-1],
            "total_return_pct": (equity_curve[-1] / equity_curve[0] - 1.0) * 100.0,
            "max_drawdown_pct": dd * 100.0,
            "sharpe": sharpe,
            "num_trades": len(trades),
            "avg_daily_turnover": (
                sum(turnover_series) / len(turnover_series) if turnover_series else 0.0
            ),
        },
    }
