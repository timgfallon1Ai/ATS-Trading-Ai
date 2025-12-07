from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal, TypedDict

# ============================================================
#  Unified Bar Format (UBF-A)
# ============================================================


class UBFBar(TypedDict):
    """Unified 1m bar format used for backtesting and live mode."""

    timestamp: int
    symbol: str

    open: float
    high: float
    low: float
    close: float
    volume: float

    # Optional enriched fields (safe for None)
    vwap: float | None
    sentiment: float | None
    news_score: float | None


# ============================================================
#  Strategy Signals
# ============================================================


class StrategySignal(TypedDict):
    """Output of 1 strategy for 1 symbol."""

    symbol: str
    direction: Literal["long", "short", "flat"]
    confidence: float
    timestamp: int


# ============================================================
#  Analyst Output
# ============================================================


class AnalystOutput(TypedDict):
    """What AnalystEngine produces per bar.
    Multiple strategies → aggregated dict.
    """

    signals: Dict[str, StrategySignal]


# ============================================================
#  Risk Manager Output
# ============================================================


class RiskOutput(TypedDict):
    """Unified output from RiskManager.
    The posture system decides whether reversals are allowed.
    """

    allowed: bool
    adjusted_signal: StrategySignal | None
    posture: Literal["cautious", "neutral", "aggressive"]


# ============================================================
#  Position Sizing Output
# ============================================================


@dataclass
class SizedPosition:
    symbol: str
    target_qty: float
    reason: str
    timestamp: int


# ============================================================
#  Execution Model Result (next-bar open)
# ============================================================


@dataclass
class ExecutedTrade:
    symbol: str
    qty: float
    price: float
    timestamp: int
    reason: str


# ============================================================
#  Portfolio State Snapshot
# ============================================================


@dataclass
class PortfolioSnapshot:
    equity: float
    cash: float
    positions: Dict[str, float]
    timestamp: int
