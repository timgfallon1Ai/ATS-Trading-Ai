# ats/backtester2/core/bar.py

from __future__ import annotations

from typing import Dict, TypedDict


class Bar(TypedDict, total=False):
    """Unified Bar Framework (UBF) standard bar format.
    Every subsystem in the ATS engine uses this exact structure.
    """

    timestamp: float
    symbol: str

    # OHLCV
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: float

    # Microstructure
    bid: float
    ask: float

    # UBF pipeline metadata
    features: Dict[str, float]
    analyst: Dict[str, float]
    signals: Dict[str, float]
    risk: Dict[str, float]
    allocations: Dict[str, float]
