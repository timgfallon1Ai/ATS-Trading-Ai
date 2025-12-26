from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class LiveConfig:
    # Trading universe
    symbols: List[str]

    # Data & broker selection
    market_data: str = "polygon"  # polygon | mock
    broker: str = "paper"  # paper | ibkr

    # Loop control
    poll_seconds: float = 5.0
    max_ticks: Optional[int] = None

    # Safety
    execute: bool = False  # if False, do not place orders (log only)
    flatten_on_kill: bool = True

    # Strategy (Phase 15.1: buy-and-hold only)
    strategy: str = "buy_and_hold"
    notional_per_symbol: float = 100.0
    allow_fractional: bool = False

    # Mock market-data (used only when market_data == "mock")
    mock_prices: Optional[Dict[str, float]] = None

    # Operational metadata
    run_tag: str = "live"
