# ats/backtester2/backtest_config.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class BacktestConfig:
    """Central configuration controlling BT-2A.

    The defaults here are safe, but you will override them dynamically.
    """

    # SYMBOLS + DATE RANGE
    symbols: List[str] = field(default_factory=lambda: ["AAPL"])
    start: Optional[int] = None
    end: Optional[int] = None

    # INITIAL CAPITAL
    initial_equity: float = 100_000.0

    # ORDERING
    max_position_size: float = 0.10  # 10% of equity per position
    risk_budget: float = 0.02  # total portfolio-level risk per bar
    leverage: float = 1.0

    # FEATURE + SIGNAL CONTROLS
    feature_window: int = 20
    smoothing: float = 0.25

    # EXECUTION SIM
    fill_model: str = "mid"
    slip_bps: float = 1.0
    latency_ms: int = 0

    # MARK-TO-MARKET
    price_mode: str = "close"  # (open/close/hlc3)

    # ANALYZER
    bar_limit: Optional[int] = None
