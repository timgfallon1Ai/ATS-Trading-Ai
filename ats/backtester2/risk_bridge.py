from __future__ import annotations

from typing import Any, Mapping, Sequence

from ats.risk_manager.risk_manager import RiskManager


def feed_allocations_to_risk(
    batch: Mapping[str, Any],
    risk_manager: RiskManager,
    base_capital: float,
) -> None:
    """Bridge Aggregator.prepare_batch(...) output into the RiskManager.

    Expected `batch` shape:
      - batch["allocations"] is a list of per-symbol allocation dicts
        (see ats.types.AggregatedAllocation)

    The RiskManager keeps the latest RM-3 weights internally on:
      - risk_manager.latest_symbol_weights
    """
    allocations = batch.get("allocations", [])
    if not isinstance(allocations, Sequence):
        return
    if not allocations:
        return

    # Delegate bridge + RM3 evaluation to the RiskManager itself.
    risk_manager.run_allocation_batch(allocations, base_capital=base_capital)  # type: ignore[arg-type]
