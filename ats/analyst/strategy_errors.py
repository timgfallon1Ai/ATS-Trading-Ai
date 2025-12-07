"""Centralized exceptions used throughout the Analyst subsystem.
Having one error taxonomy ensures the entire Analyst layer remains stable
and avoids circular imports or inconsistent error handling.
"""


class StrategyError(Exception):
    """Base class for all strategy-related errors."""


class StrategyNotFoundError(StrategyError):
    """Raised when a strategy name does not exist in the registry."""


class StrategyLoadError(StrategyError):
    """Raised when a strategy module exists but fails to load or initialize."""


class InvalidFeatureError(StrategyError):
    """Raised when a strategy receives malformed or missing features."""


class StrategyExecutionError(StrategyError):
    """Raised when a strategy generate() method fails internally."""


class DuplicateStrategyError(StrategyError):
    """Raised when the registry attempts to register a strategy twice."""
