from __future__ import annotations

from typing import Any, Dict

from ats.risk_manager.risk_manager import RiskManager
from ats.risk_manager.rm_bridge import batch_to_capital_packets


def feed_allocations_to_risk(
    batch: Dict[str, Any],
    risk_manager: RiskManager,
    base_capital: float,
) -> None:
    """Bridge Aggregator.prepare_batch(...) output into the RiskManager.

    - `batch` is the full dict returned by Aggregator.prepare_batch(...).
      It must contain an `allocations` key with AggregatedAllocation entries.
    - We convert that into CapitalAllocPacket objects via rm_bridge.
    - Then we call RiskManager.run_capital_batch(...) so RM3/RM4 see them.
    """
    packets = batch_to_capital_packets(batch=batch, base_capital=base_capital)
    if not packets:
        return

    risk_manager.run_capital_batch(packets)
