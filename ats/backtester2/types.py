from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Side = Literal["buy", "sell"]


@dataclass
class Bar:
    """
    Minimal OHLCV bar used by the backtester.

    - timestamp: ISO 8601 string (e.g. "2025-12-02T09:30:00Z").
    - symbol: Trading symbol (e.g. "AAPL").
    - open/high/low/close: Bar prices.
    - volume: Optional, for now we don't enforce or use it heavily.
    """

    timestamp: str
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


from datetime import datetime
from typing import Any, Dict, Mapping, Optional, TypedDict, Literal

# --------------------------------------------------------------------------------------
# Analyst / signal-related types used by backtester2 and bt_validation
# --------------------------------------------------------------------------------------


Side = Literal["long", "short", "flat"]


class RawSignal(TypedDict, total=False):
    """
    Per-strategy signal on a single bar.

    This is intentionally loose (total=False) so Pylance is happy even if
    individual strategies don't populate every field.
    """

    symbol: str
    timestamp: datetime
    strategy: str
    side: Side
    score: float
    confidence: float
    weight: float
    metadata: Dict[str, Any]


class CombinedSignal(TypedDict, total=False):
    """
    Aggregated signal across many strategies for a symbol/bar.

    This is what the risk manager / sizing layer should ultimately see.
    """

    symbol: str
    timestamp: datetime
    side: Side
    score: float
    confidence: float

    # Optional: how much each strategy contributed to the final decision,
    # typically as normalized weights or scores.
    per_strategy: Dict[str, float]

    # Optional: raw underlying strategy signals keyed by strategy_id.
    raw_signals: Dict[str, RawSignal]

    # Anything else we might want to hang off the signal.
    metadata: Dict[str, Any]


# Numerical features extracted from bars / fundamentals / news, etc.
FeatureSet = Mapping[str, float]


# --------------------------------------------------------------------------------------
# Bridge aliases for order/fill types
# --------------------------------------------------------------------------------------

# We prefer to reuse the canonical engine-level definitions from ats.types if
# they exist. If they don't, we fall back to simple local TypedDict stubs so
# that bt_validation and friends have something to type-check against.


try:
    from ats.types import (  # type: ignore[import]
        Fill as _EngineFill,
        SizedOrder as _EngineSizedOrder,
    )

    Fill = _EngineFill
    SizedOrder = _EngineSizedOrder

except ImportError:

    class Fill(TypedDict, total=False):
        symbol: str
        timestamp: datetime
        side: Literal["buy", "sell"]
        quantity: float
        price: float
        commission: float
        metadata: Dict[str, Any]

    class SizedOrder(TypedDict, total=False):
        symbol: str
        timestamp: datetime
        side: Literal["buy", "sell"]
        quantity: float
        limit_price: Optional[float]
        metadata: Dict[str, Any]
