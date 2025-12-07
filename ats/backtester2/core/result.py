# ats/backtester2/core/result.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .ledger import Transaction


@dataclass
class BacktestResult:
    """Returned after the entire backtest completes."""

    equity_curve: List[float]
    transactions: List[Transaction]
    metadata: dict = field(default_factory=dict)
