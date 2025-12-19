"""ats.backtester2

A lightweight, stable backtesting entrypoint.

Run:
    python -m ats.backtester2.run --symbol AAPL --days 200
"""

from .backtest_config import BacktestConfig
from .engine import BacktestEngine, BacktestResult
from .types import Bar

__all__ = ["BacktestConfig", "BacktestEngine", "BacktestResult", "Bar"]
