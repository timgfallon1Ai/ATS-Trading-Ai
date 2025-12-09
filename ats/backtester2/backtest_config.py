from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BacktestConfig:
    """
    Configuration for a single-symbol backtest.

    This is intentionally minimal for T2. As we integrate more complex
    components (multi-symbol, risk, fees, etc.) we can extend this
    dataclass without breaking existing call sites.
    """

    symbol: str
    starting_capital: float = 100_000.0
    bar_limit: int | None = None  # optional cap on number of bars to process
