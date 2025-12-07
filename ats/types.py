from __future__ import annotations

from typing import Any, Dict, List, TypedDict

from typing_extensions import NotRequired

# ------------------------------------------------------------
# Feature Types
# ------------------------------------------------------------


class FeatureVector(TypedDict):
    """A vector of analyst features for a single symbol."""

    vol: float
    ret: float
    entropy: float
    regime_prob: NotRequired[float]
    additional: NotRequired[Dict[str, float]]


# FeatureMap is **not** a TypedDict – it is a true mapping
FeatureMap = Dict[str, FeatureVector]


# ------------------------------------------------------------
# Aggregated Allocation (input to RM-MASTER)
# ------------------------------------------------------------


class AggregatedAllocation(TypedDict):
    symbol: str
    score: float
    confidence: float
    timestamp: str

    # optional analytics / strategy info
    weight: NotRequired[float]
    strategy: NotRequired[str]
    metadata: NotRequired[Dict[str, Any]]

    # required by RM-3 and RM-4
    strategy_breakdown: NotRequired[Dict[str, float]]
    target_qty: NotRequired[float]


# ------------------------------------------------------------
# RM-2 Predictive Packet
# ------------------------------------------------------------


class PredictivePacket(TypedDict):
    regime: str
    risk_score: float
    details: NotRequired[Dict[str, Any]]


# ------------------------------------------------------------
# RM-4 Posture Packet
# ------------------------------------------------------------


class PosturePacket(TypedDict):
    posture: str  # NORMAL / HEIGHTENED / ALERT / HALT
    anomaly_score: float
    drift_score: float
    notes: NotRequired[List[str]]


# ------------------------------------------------------------
# RM-5 Execution Packet (Unified for Simulator + Trader)
# ------------------------------------------------------------


class ExecutionPacket(TypedDict):
    symbol: str
    requested_qty: float
    filled_qty: float
    slippage: float
    latency_ms: float
    posture: str
    timestamp: str

    # Optional — for ExecutionSimulator / Trader
    side: NotRequired[str]
    size: NotRequired[float]
    price: NotRequired[float]

    # Governance / logs
    notes: NotRequired[List[str]]


# ------------------------------------------------------------
# RM-6 Portfolio Packet
# ------------------------------------------------------------


class PortfolioPacket(TypedDict):
    equity: float
    unrealized_pnl: float
    health: float
    reputation: float
    components: NotRequired[Dict[str, Any]]


# ------------------------------------------------------------
# RM-7 Governance Packet
# ------------------------------------------------------------


class GovernancePacket(TypedDict):
    warnings: List[str]
    posture_transitions: List[str]
    rejected_allocations: List[str]
    notes: NotRequired[List[str]]


# ------------------------------------------------------------
# Final Per-Symbol Output (RM-1 → RM-7)
# ------------------------------------------------------------


class RiskPacket(TypedDict):
    symbol: str
    strategy: str
    timestamp: str

    quantity: Dict[str, float]

    predictive: PredictivePacket
    posture: PosturePacket
    execution: ExecutionPacket
    portfolio: PortfolioPacket
    governance: GovernancePacket


# ------------------------------------------------------------
# Batch Output (all symbols)
# ------------------------------------------------------------


class RiskBatchOutput(TypedDict):
    timestamp: str
    allocations: List[RiskPacket]
    posture_state: str
    equity: float
    warnings: List[str]
    governance: GovernancePacket
