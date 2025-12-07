"""ATS — Autonomous Trading System
Unified package initializer.
"""

from . import (
    adaptation,
    aggregator,
    analyst,
    backtester2,
    dashboard,
    data_ingestion,
    data_validation,
    event_bus,
    risk_manager,
    trader,
    types,
)
from .core import config

__all__ = [
    "types",
    "config",
    "event_bus",
    "analyst",
    "aggregator",
    "risk_manager",
    "trader",
    "backtester2",
    "data_ingestion",
    "data_validation",
    "dashboard",
    "adaptation",
]
