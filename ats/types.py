"""
Shared type contracts for the ATS.

These types are used to connect:
- Analyst / Aggregator output
- RM-2 predictive models
- RM-3 capital allocation
- RM-4 posture / execution filters
- Backtester and live trader orchestration
"""

from __future__ import annotations

from typing import Any, Dict, List, TypedDict
from typing_extensions import NotRequired


# -----------------------------------------------------------------------------
# 1. Feature-level contracts (Analyst / Aggregator)
# -----------------------------------------------------------------------------


class FeatureVector(TypedDict):
    """
    A single feature snapshot for a symbol at a given timestamp.

    This is the canonical structure passed between the analyst layer
    and any downstream consumers that operate at the "features" level.
    """

    symbol: str
    timestamp: str  # ISO-8601
    features: Dict[str, float]


# A simpler alias used throughout analyst / strategy code.
FeatureMap = Dict[str, float]


class AggregatedAllocation(TypedDict):
    """
    Aggregated signal / allocation coming out of the analyst + aggregator stack.

    This is the primary input into RM-3 (capital allocator) and RM-4 (posture).
    """

    # Core required fields
    symbol: str
    score: float
    confidence: float
    timestamp: str

    # Optional analytics / strategy info
    weight: NotRequired[float]
    strategy: NotRequired[str]
    metadata: NotRequired[Dict[str, Any]]

    # Required by RM-3 and RM-4 (but filled in by upstream components)
    strategy_breakdown: NotRequired[Dict[str, float]]
    target_qty: NotRequired[float]


# -----------------------------------------------------------------------------
# 2. Predictive risk layer (RM-2)
# -----------------------------------------------------------------------------


class PredictivePacket(TypedDict, total=False):
    """
    Output of the RM-2 predictive engine for a single symbol.

    All fields are optional because different models may emit different subsets.
    """

    symbol: str
    timestamp: str  # ISO-8601

    # Vol / drawdown style metrics
    predicted_vol: float  # e.g. annualized or per-bar
    predicted_drawdown: float  # e.g. expected max drawdown over horizon

    # Regime / risk scoring
    risk_score: float  # normalized [0, 1] riskiness
    regime: str  # e.g. "bull", "bear", "sideways"
    confidence: float  # model confidence in the regime / risk score


# -----------------------------------------------------------------------------
# 3. Capital allocation layer (RM-3)
# -----------------------------------------------------------------------------


class CapitalAllocPacket(TypedDict, total=False):
    """
    Capital allocation decision for a single symbol, as produced by RM-3.

    This is the bridge between score-space (AggregatedAllocation) and
    dollar-space / notional limits for execution.
    """

    symbol: str

    # Core decision: how many dollars of book to allocate to this symbol
    target_dollars: float

    # Risk-aware annotation (generally derived from RM-2 output)
    predicted_risk: float  # e.g. per-position risk fraction
    risk_score: float  # copy-through or transformation of PredictivePacket.risk_score
    regime: str  # copy-through of PredictivePacket.regime

    # Optional metadata / audit information
    timestamp: NotRequired[str]
    notes: NotRequired[str]


# -----------------------------------------------------------------------------
# 4. Posture, execution filters, portfolio & governance (RM-4+)
# -----------------------------------------------------------------------------


class PosturePacket(TypedDict, total=False):
    """
    Posture / envelope-level view for a symbol or the whole book.

    This is where RM-4 expresses high-level constraints such as:
    - net / gross exposure
    - posture state (off / cautious / normal / aggressive)
    """

    symbol: str

    # Exposure metrics
    net_exposure: float  # signed notional
    gross_exposure: float  # absolute notional
    max_drawdown: float  # observed or simulated

    # Posture state
    posture: str  # e.g. "off", "cautious", "normal", "aggressive"
    posture_confidence: float  # confidence in posture choice

    timestamp: str


class ExecutionPacket(TypedDict, total=False):
    """
    Execution-level risk guidance for a specific intent or order.

    This envelope is used by RM-5 execution filters and by the trader
    to understand slippage- and impact-aware constraints.
    """

    symbol: str
    side: str  # "buy" or "sell"

    # Dollar and quantity limits
    order_notional: float
    max_notional: float
    max_qty: float

    # Microstructure / cost estimates
    slip_bps: float  # expected slippage in basis points
    impact_bps: float  # expected market impact in basis points

    # Hard kill switches
    cancel: bool  # if True, block this order
    reason: str  # human-readable explanation

    timestamp: str


class PortfolioPacket(TypedDict, total=False):
    """
    Snapshot of portfolio health metrics for a symbol or book-wide.

    This is the primary contract for RM-6 (portfolio health) outputs.
    """

    # Basic P&L and equity breakdown
    equity: float
    cash: float
    realized_pnl: float
    unrealized_pnl: float

    # Optional per-symbol detail
    symbol: str
    symbol_qty: float
    symbol_notional: float

    timestamp: str


class GovernancePacket(TypedDict, total=False):
    """
    Governance and oversight annotations, primarily for RM-7.

    This structure is intentionally loose: we care more about human-auditable
    strings than strict numeric schemas.
    """

    warnings: List[str]
    posture_transitions: List[str]
    rejected_allocations: List[str]
    notes: List[str]


# -----------------------------------------------------------------------------
# 5. Unified risk envelope (RM master / orchestrator)
# -----------------------------------------------------------------------------


class RiskPacket(TypedDict, total=False):
    """
    Unified, per-symbol risk envelope flowing through the RM master.

    Each sub-packet can be omitted if that layer is disabled or has no opinion.
    """

    symbol: str

    predictive: PredictivePacket
    capital: CapitalAllocPacket
    posture: PosturePacket
    execution: ExecutionPacket
    portfolio: PortfolioPacket
    governance: GovernancePacket


class RiskBatchOutput(TypedDict):
    """
    Batch-style risk output for a single evaluation pass.

    - by_symbol: symbol -> RiskPacket
    - governance: batch-level governance metadata
    """

    by_symbol: Dict[str, RiskPacket]
    governance: GovernancePacket

    # Optional batch metadata (timestamps, run identifiers, etc.)
    ts: NotRequired[str]
    asof: NotRequired[str]
    metadata: NotRequired[Dict[str, Any]]


# Convenience aliases used throughout the codebase
RiskEnvelope = Dict[str, RiskPacket]
ExecutionFilterPacket = Dict[str, Any]
HealthPacket = Dict[str, Any]


__all__ = [
    # Feature / analyst layer
    "FeatureVector",
    "FeatureMap",
    "AggregatedAllocation",
    # Predictive layer
    "PredictivePacket",
    # Capital allocation
    "CapitalAllocPacket",
    # Posture / execution / portfolio / governance
    "PosturePacket",
    "ExecutionPacket",
    "PortfolioPacket",
    "GovernancePacket",
    # Unified risk envelope
    "RiskPacket",
    "RiskBatchOutput",
    "RiskEnvelope",
    "ExecutionFilterPacket",
    "HealthPacket",
]
