import math
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class BacktestMetrics:
    n_bars: int
    start_equity: float
    end_equity: float
    total_return: float  # fraction, e.g. 0.10 = +10%
    max_drawdown: float  # fraction, e.g. 0.15 = -15% peak->trough
    ann_vol: float  # annualized volatility (naive)
    sharpe: float  # naive Sharpe (rf=0)


def compute_backtest_metrics(
    portfolio_history: List[Dict[str, Any]],
    periods_per_year: int = 252,
) -> BacktestMetrics:
    equities: List[float] = []
    for snap in portfolio_history or []:
        if isinstance(snap, dict) and "equity" in snap:
            try:
                equities.append(float(snap["equity"]))
            except Exception:
                pass

    if len(equities) < 2:
        start = equities[0] if equities else 0.0
        return BacktestMetrics(
            n_bars=len(equities),
            start_equity=start,
            end_equity=start,
            total_return=0.0,
            max_drawdown=0.0,
            ann_vol=0.0,
            sharpe=0.0,
        )

    rets: List[float] = []
    for prev, cur in zip(equities[:-1], equities[1:]):
        if prev == 0:
            rets.append(0.0)
        else:
            rets.append(cur / prev - 1.0)

    mean = sum(rets) / len(rets) if rets else 0.0
    var = sum((r - mean) ** 2 for r in rets) / len(rets) if rets else 0.0
    std = math.sqrt(var)

    ann_vol = std * math.sqrt(periods_per_year) if std > 0 else 0.0
    sharpe = (mean / std) * math.sqrt(periods_per_year) if std > 0 else 0.0

    peak = equities[0]
    max_dd = 0.0
    for e in equities:
        peak = max(peak, e)
        if peak > 0:
            dd = (peak - e) / peak
            max_dd = max(max_dd, dd)

    total_return = equities[-1] / equities[0] - 1.0 if equities[0] != 0 else 0.0

    return BacktestMetrics(
        n_bars=len(equities),
        start_equity=equities[0],
        end_equity=equities[-1],
        total_return=total_return,
        max_drawdown=max_dd,
        ann_vol=ann_vol,
        sharpe=sharpe,
    )
