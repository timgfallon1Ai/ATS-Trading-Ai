from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Sequence, TypedDict

try:  # Optional import for shared backtester types; safe fallback if not present.
    from ats.backtester2.types import CombinedSignal  # type: ignore[import]
except Exception:  # pragma: no cover - used only when backtester types are unavailable.

    class CombinedSignal(TypedDict, total=False):
        """Fallback CombinedSignal definition for type checking and tooling."""

        symbol: str
        timestamp: str
        direction: str  # "long" | "short" | "flat"
        score: float
        confidence: float
        source: str
        metadata: Dict[str, Any]


# At runtime we treat allocations as generic mappings. The "real" shape lives in
# ats.types.AggregatedAllocation, but importing it here would introduce an
# unnecessary dependency for the synthetic backtester.
AggregatedAllocation = Mapping[str, Any]


@dataclass
class AggregatorConfig:
    """Configuration for mapping analyst allocations to trading signals.

    This is intentionally conservative; live trading can tighten thresholds later.
    """

    long_threshold: float = 0.15
    short_threshold: float = -0.15
    min_confidence: float = 0.05
    max_weight: float = 1.0
    min_weight: float = -1.0


@dataclass
class Aggregator:
    """Lightweight aggregation and normalization layer for analyst allocations.

    In the synthetic backtester, we:
      * Take per-bar AggregatedAllocation objects (one per symbol).
      * Map them into discrete CombinedSignal directions for the trading simulation.
      * Normalize numeric fields for downstream risk-manager consumption.
    """

    config: AggregatorConfig = field(default_factory=AggregatorConfig)

    def _direction_from_score(self, score: float, confidence: float) -> str:
        """Map continuous score + confidence into a discrete trade direction."""
        if confidence < self.config.min_confidence:
            return "flat"
        if score >= self.config.long_threshold:
            return "long"
        if score <= self.config.short_threshold:
            return "short"
        return "flat"

    def combine_allocation(self, alloc: AggregatedAllocation) -> CombinedSignal:
        """Convert a single AggregatedAllocation into a CombinedSignal.

        The allocation is treated as read-only; we never mutate the input mapping.
        """

        symbol = str(alloc.get("symbol", ""))
        timestamp = str(alloc.get("timestamp", ""))
        score_raw = alloc.get("score", 0.0) or 0.0
        conf_raw = alloc.get("confidence", 0.0) or 0.0

        score = float(score_raw)
        confidence = float(conf_raw)

        direction = self._direction_from_score(score, confidence)

        source = str(alloc.get("source") or alloc.get("strategy") or "analyst")
        metadata_val = alloc.get("metadata") or {}
        metadata = (
            dict(metadata_val)
            if isinstance(metadata_val, dict)
            else {"raw_metadata": metadata_val}
        )

        signal: CombinedSignal = {
            "symbol": symbol,
            "timestamp": timestamp,
            "direction": direction,
            "score": score,
            "confidence": confidence,
            "source": source,
            "metadata": metadata,
        }
        return signal

    def prepare_batch(
        self, allocations: Sequence[AggregatedAllocation]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Normalize a sequence of allocations for logging and risk-manager consumption.

        Returns a dictionary with:
          * "combined_signals": List[CombinedSignal]
          * "allocations":     List[dict] (normalized copies of the input allocations)

        The output structure is intentionally plain so it can be serialized directly into
        JSON logs or pushed over the RM bridge without further adaptation.
        """

        combined_signals: List[Dict[str, Any]] = []
        normalized_allocs: List[Dict[str, Any]] = []

        for alloc in allocations:
            # Defensive copy so callers can pass real AggregatedAllocation instances or plain dicts.
            norm: Dict[str, Any] = {
                "symbol": str(alloc.get("symbol", "")),
                "timestamp": str(alloc.get("timestamp", "")),
                "score": float(alloc.get("score", 0.0) or 0.0),
                "confidence": float(alloc.get("confidence", 0.0) or 0.0),
            }

            # Strategy-level breakdown (optional but very useful for RM3/RM4).
            strategy_breakdown = alloc.get("strategy_breakdown")
            if isinstance(strategy_breakdown, Mapping):
                norm["strategy_breakdown"] = {
                    str(k): float(v) for k, v in strategy_breakdown.items()
                }

            # Optional sizing / weight information, clamped to config bounds.
            weight = alloc.get("weight")
            if weight is not None:
                w = float(weight)
                w = max(self.config.min_weight, min(self.config.max_weight, w))
                norm["weight"] = w

            if "target_qty" in alloc and alloc.get("target_qty") is not None:
                norm["target_qty"] = float(alloc["target_qty"])  # type: ignore[index]

            if "strategy" in alloc and alloc.get("strategy") is not None:
                norm["strategy"] = str(alloc["strategy"])

            metadata_val = alloc.get("metadata")
            if isinstance(metadata_val, Mapping):
                norm["metadata"] = dict(metadata_val)

            normalized_allocs.append(norm)
            combined_signals.append(self.combine_allocation(norm))

        return {
            "combined_signals": combined_signals,
            "allocations": normalized_allocs,
        }

    def to_risk_batch(
        self, allocations: Sequence[AggregatedAllocation]
    ) -> List[Dict[str, Any]]:
        """Helper for RM bridge: return just the normalized allocations list.

        This keeps the risk-manager interface focused on allocations while still
        allowing the backtester and logging layers to use the richer batch structure.
        """

        batch = self.prepare_batch(allocations)
        return batch["allocations"]
