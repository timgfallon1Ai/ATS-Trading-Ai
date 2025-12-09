"""
Backtester v2 core.

This module provides a thin, stable interface for running backtests
programmatically or via:

    python -m ats.backtester2.run --symbol AAPL

The key types exported are:

- BacktestConfig: Configuration for a single backtest run.
- BacktestEngine: The core engine that loops over bars and calls Trader.
- BacktestResult: Container for trade and portfolio history.
"""

from .backtest_config import BacktestConfig
from .engine import BacktestEngine, BacktestResult

__all__ = ["BacktestConfig", "BacktestEngine", "BacktestResult"]
