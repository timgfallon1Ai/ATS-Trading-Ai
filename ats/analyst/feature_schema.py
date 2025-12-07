"""Feature Schema — The strongly-typed interface between
the UBF ingestion layer, AnalystEngine, and all strategies.

This file defines:
- The Feature type (TypedDict)
- Allowed fields & their types
- Optional / required inputs
- The normalized format all strategies must consume

This ensures:
✔ Zero drift across strategies
✔ No undefined TypedDict keys
✔ Predictable structure for AnalystEngine
✔ Full Pylance/type checker satisfaction
"""

from __future__ import annotations

from typing import Any, Dict, Optional, TypedDict

# ============================================================
# Core Feature Schema
# ============================================================


class Feature(TypedDict, total=False):
    """Each bar/row delivered to AnalystEngine has this structure.

    total=False means:
    - Only required keys MUST appear
    - Additional optional fields are allowed
    """

    # --------------------------------------------------------
    # REQUIRED FIELDS — every strategy receives these
    # --------------------------------------------------------
    symbol: str
    timestamp: int  # UNIX epoch ms
    close: float
    open: float
    high: float
    low: float
    volume: float

    # --------------------------------------------------------
    # OPTIONAL FIELDS — UBF may include these depending on data source
    # Strategies can use them if present
    # --------------------------------------------------------
    vwap: Optional[float]
    returns_1m: Optional[float]
    returns_5m: Optional[float]
    volatility: Optional[float]

    # Macro signals
    macro_score: Optional[float]

    # Sentiment signals
    sentiment_score: Optional[float]

    # Fundamental / news events
    earnings_flag: Optional[int]
    earnings_score: Optional[float]

    # Pattern recognition fields
    pattern_tag: Optional[str]

    # ML-driven factors
    factor_scores: Optional[Dict[str, float]]

    # Raw vendor-specific extra payload
    meta: Optional[Dict[str, Any]]


# ============================================================
# FeatureBatch
# ============================================================


class FeatureBatch(TypedDict):
    """A batch of features for a single symbol.
    Used heavily by AnalystEngine and backtester.
    """

    symbol: str
    bars: list[Feature]  # ordered oldest → newest


# ============================================================
# Sanity check helpers for ingestion layer
# ============================================================

REQUIRED_FEATURE_KEYS = [
    "symbol",
    "timestamp",
    "close",
    "open",
    "high",
    "low",
    "volume",
]


def validate_required_fields(f: Feature) -> None:
    """Raises if any required feature field is missing."""
    for key in REQUIRED_FEATURE_KEYS:
        if key not in f:
            raise KeyError(f"Feature missing required field: {key}")
