from __future__ import annotations

from typing import Any, Dict, List, Set

from ats.types import AggregatedAllocation, CapitalAllocPacket

DEFAULT_BASE_CAPITAL = 1_000_000.0


def _compute_symbol_weights(
    allocations: List[AggregatedAllocation],
) -> Dict[str, float]:
    """Compute normalized per-symbol weights from aggregated allocations.

    Priority:
    - If an allocation has an explicit `weight`, use that.
    - Otherwise fall back to |score| * confidence.
    - Normalize across symbols so weights sum to 1.
    - If everything is zero / empty, fall back to equal weights.
    """
    weights: Dict[str, float] = {}

    for alloc in allocations:
        symbol = alloc["symbol"]
        w = alloc.get("weight")

        if w is None:
            w = float(abs(alloc["score"]) * alloc["confidence"])

        if w <= 0.0:
            continue

        weights[symbol] = weights.get(symbol, 0.0) + float(w)

    if not weights:
        symbols: Set[str] = {a["symbol"] for a in allocations}
        if not symbols:
            return {}
        equal = 1.0 / float(len(symbols))
        return {s: equal for s in symbols}

    total = sum(weights.values())
    if total <= 0.0:
        return weights

    for sym in list(weights.keys()):
        weights[sym] = weights[sym] / total

    return weights


def allocations_to_capital_packets(
    allocations: List[AggregatedAllocation],
    base_capital: float = DEFAULT_BASE_CAPITAL,
) -> List[CapitalAllocPacket]:
    """Convert AggregatedAllocation entries into RM3-style capital packets.

    Output contract:
      - target_dollars is signed (score direction preserved).
      - capital is also included as a deprecated alias for backward compatibility.
    """
    symbol_weights = _compute_symbol_weights(allocations)
    if not symbol_weights:
        return []

    packets: List[CapitalAllocPacket] = []

    for alloc in allocations:
        symbol = alloc["symbol"]
        if symbol not in symbol_weights:
            continue

        weight = float(symbol_weights[symbol])
        direction = 1.0 if float(alloc["score"]) >= 0.0 else -1.0
        target_dollars = float(base_capital) * weight * direction

        packets.append(
            {
                "symbol": symbol,
                "target_dollars": target_dollars,
                "capital": target_dollars,  # deprecated alias
                "score": float(alloc["score"]),
                "confidence": float(alloc["confidence"]),
                "strategy_breakdown": dict(alloc.get("strategy_breakdown") or {}),
                "metadata": dict(alloc.get("metadata") or {}),
                "timestamp": str(alloc.get("timestamp") or ""),
            }
        )

    return packets


def batch_to_capital_packets(
    batch: Dict[str, Any],
    base_capital: float = DEFAULT_BASE_CAPITAL,
) -> List[CapitalAllocPacket]:
    """Convenience: take the full Aggregator.prepare_batch(...) result.

    Expects a dict with an `allocations` key containing AggregatedAllocation entries.
    This keeps the Risk Manager side decoupled from the exact batch structure
    Aggregator uses.
    """
    allocations: List[AggregatedAllocation] = batch.get("allocations", [])
    return allocations_to_capital_packets(
        allocations=allocations,
        base_capital=base_capital,
    )
