from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from ats.backtester2.types import Bar, SizedOrder
from ats.types import CapitalAllocPacket
from .rm3_capital.capital_allocator import CapitalAllocator, CapitalAllocatorConfig


@dataclass
class RiskConfig:
    """Baseline risk configuration.

    This is intentionally simple for now; RM1/RM2/RM3/RM4 can grow around it.
    """

    # Per-order and per-position limits (not yet strictly enforced in apply).
    max_single_order_notional: float = 50_000.0
    max_position_notional: float = 250_000.0

    # Max daily loss (placeholder; you can wire this to PnL tracking later).
    max_daily_loss: float = 50_000.0

    # Base capital used when interpreting allocations.
    base_capital: float = 1_000_000.0


@dataclass
class RiskManager:
    """Top-level risk manager façade.

    - RM1/RM2 style per-order gating happens in `apply`.
    - RM3 capital allocation happens in `run_capital_batch`.
    - RM4 posture / portfolio health can consume `latest_symbol_weights`
      plus the CapitalAllocPacket metadata as needed.
    """

    config: RiskConfig = field(default_factory=RiskConfig)
    capital_allocator: CapitalAllocator = field(
        default_factory=lambda: CapitalAllocator(CapitalAllocatorConfig())
    )

    # Simple counters used by the backtester.
    bars_evaluated: int = 0
    orders_blocked: int = 0

    # Latest RM3 output: symbol -> target weight.
    latest_symbol_weights: Dict[str, float] = field(default_factory=dict)

    def apply(
        self,
        symbol: str,
        bar: Bar,
        orders: List[SizedOrder],
    ) -> List[SizedOrder]:
        """RM1/RM2 style per-order risk checks.

        For now this is a baseline pass-through that just increments counters.
        You can incrementally add notional / exposure / loss checks here.
        """
        self.bars_evaluated += 1

        # Example placeholder: keep all orders but track how many we "would" block.
        # You can flesh this out later using self.config and self.latest_symbol_weights.
        return orders

    def run_capital_batch(self, packets: List[CapitalAllocPacket]) -> None:
        """RM3 entrypoint: consume aggregator allocations as CapitalAllocPacket list."""
        if not packets:
            return

        weights = self.capital_allocator.allocate(packets)
        self.latest_symbol_weights = weights

        # Hook point: RM4 / portfolio health scoring can be driven from `weights`
        # plus the strategy_breakdown metadata contained in each packet.

    def summary(self) -> Dict[str, float]:
        """Small helper used by the backtester to log risk activity."""
        return {
            "bars_evaluated": float(self.bars_evaluated),
            "orders_blocked": float(self.orders_blocked),
        }
