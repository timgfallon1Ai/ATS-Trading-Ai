cat > ats / backtester2 / schema.py << "PY"
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Bar:
    """Simple OHLCV bar used by Backtester2 tests and engine."""

    timestamp: str
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class BacktestConfig:
    """
    Minimal backtest configuration for Backtester2.

    Tests rely on these fields existing:
    - symbol
    - starting_capital
    - bar_limit
    """

    symbol: str
    starting_capital: float = 100_000.0
    bar_limit: Optional[int] = None

    # Optional metadata (safe / backwards-compatible)
    strategy: str = "ma"
    days: Optional[int] = None
    enable_risk: bool = True


@dataclass
class BacktestResult:
    """
    Result container returned by Backtester2.

    Tests rely on:
    - .config
    - .portfolio_history
    - .final_portfolio
    """

    config: BacktestConfig
    portfolio_history: List[Dict[str, Any]] = field(default_factory=list)
    trade_history: List[Dict[str, Any]] = field(default_factory=list)
    final_portfolio: Optional[Dict[str, Any]] = None


PY
