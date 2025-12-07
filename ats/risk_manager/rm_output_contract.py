from __future__ import annotations

from typing import Dict, List, TypedDict

# ============================================================
# RM MASTER → TRADER CONTRACT
# The single unified structure for every allocation.
# ============================================================


class ExecutionMeta(TypedDict):
    """RM-5 execution metadata."""

    slippage: float  # 0.0–1.0
    latency: float  # simulated latency seconds
    fill_probability: float  # 0–1 probability


class PostureMeta(TypedDict):
    """RM-4 posture & anomaly/drift signals."""

    posture: str  # NORMAL / HEIGHTENED / ALERT / HALT
    anomaly_score: float
    drift_score: float


class PredictiveMeta(TypedDict):
    """RM-2 predictive overlays."""

    model_score: float
    volatility: float
    predicted_risk: float
    risk_score: float
    regime: str


class GovernanceMeta(TypedDict):
    """RM-7 governance & audit logging metadata."""

    warnings: List[str]
    notes: List[str]
    rule_violations: List[str]
    posture_transitions: List[str]


class PortfolioMeta(TypedDict):
    """RM-6 portfolio health & strategy-level performance."""

    portfolio_score: float
    reputation_deltas: Dict[str, float]


class RMOrderPacket(TypedDict):
    """Final RM-MASTER output structure.
    This is what TRADER receives for each symbol.
    """

    symbol: str
    target_qty: float  # final quantity after RM adjustments
    requested_dollars: float  # raw capital before RM adjustments
    confidence: float  # hybrid confidence (0–1)
    strategy_breakdown: Dict[str, float]

    # RM sub-components
    predictive: PredictiveMeta
    execution: ExecutionMeta
    posture: PostureMeta
    governance: GovernanceMeta
    portfolio: PortfolioMeta

    timestamp: str  # UTC ISO timestamp


class RMBatchOutput(TypedDict):
    """Batch-level output for all symbols in one cycle."""

    timestamp: str
    orders: List[RMOrderPacket]
    portfolio_value: float
