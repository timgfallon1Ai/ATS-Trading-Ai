from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class LiveConfig:
    # Universe / plumbing
    symbols: List[str]
    market_data: str = "polygon"  # "polygon" | "mock"
    broker: str = "paper"  # "paper" | "ibkr"
    poll_seconds: float = 5.0
    max_ticks: Optional[int] = None

    # Safety
    execute: bool = False
    flatten_on_kill: bool = True

    # Strategy selection
    strategy: str = "buy_and_hold"  # "buy_and_hold" | "analyst_ensemble"

    # Basic sizing knobs
    notional_per_symbol: float = 100.0
    allow_fractional: bool = False

    # Mock mode
    mock_prices: Optional[Dict[str, float]] = None

    # Analyst ensemble knobs (Phase 15.2)
    history_bars: int = 120
    warmup_bars: int = 30
    min_confidence: float = 0.15
    allow_short: bool = False
    rebalance_threshold_notional: float = 5.0
    log_signals: bool = False

    # Tagging
    run_tag: str = "phase15"
