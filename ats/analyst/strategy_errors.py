# ats/analyst/strategy_errors.py
from __future__ import annotations


class StrategyError(Exception):
    """Base class for all strategy-related errors."""


class StrategyConfigError(StrategyError):
    """Raised when a strategy is misconfigured or cannot be constructed."""


class StrategyRuntimeError(StrategyError):
    """Raised when a strategy fails during signal generation."""


class AnalystEngineError(Exception):
    """Base class for errors in the analyst engine."""
