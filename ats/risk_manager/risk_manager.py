from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Sequence

from ats.trader.order_types import Order
from ats.types import AggregatedAllocation, CapitalAllocPacket

# ---------------------------------------------------------------------
# RM3 allocator imports (kept resilient to signature/config evolution)
# ---------------------------------------------------------------------
try:
    from .rm3_capital.capital_allocator import CapitalAllocator, CapitalAllocatorConfig
except Exception:  # pragma: no cover
    from .rm3_capital.capital_allocator import CapitalAllocator  # type: ignore

    CapitalAllocatorConfig = None  # type: ignore[assignment]


def _make_default_allocator() -> CapitalAllocator:
    """
    Construct a CapitalAllocator with best-effort compatibility across revisions.
    """
    if CapitalAllocatorConfig is None:
        return CapitalAllocator()  # type: ignore[call-arg]
    try:
        return CapitalAllocator(CapitalAllocatorConfig())  # type: ignore[arg-type]
    except TypeError:
        return CapitalAllocator()  # type: ignore[call-arg]


# ---------------------------------------------------------------------
# RM bridge import (support both allocations_to_* and batch_to_* shapes)
# ---------------------------------------------------------------------
try:
    from .rm_bridge import allocations_to_capital_packets as _allocations_to_packets
except Exception:  # pragma: no cover
    from .rm_bridge import batch_to_capital_packets as _batch_to_packets

    def _allocations_to_packets(
        allocations: Sequence[AggregatedAllocation],
        base_capital: float,
    ) -> List[CapitalAllocPacket]:
        batch = {"allocations": list(allocations)}
        return _batch_to_packets(batch=batch, base_capital=base_capital)


# ---------------------------------------------------------------------
# Public contracts expected by ats.risk_manager.__init__
# ---------------------------------------------------------------------
@dataclass(frozen=True)
class RejectedOrder:
    order: Order
    reason: str


@dataclass
class RiskDecision:
    """Result of evaluating a batch of orders at a bar/timestamp."""

    timestamp: str
    symbol: str | None = None

    accepted_orders: List[Order] = field(default_factory=list)
    rejected_orders: List[RejectedOrder] = field(default_factory=list)

    # Extra debug/audit metadata
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskConfig:
    """Baseline RiskManager config.

    Intentionally conservative/simple.
    RM-2+ can add overlays without breaking this contract.
    """

    # The notional "book" size used when interpreting RM3 weights.
    base_capital: float = 1_000_000.0

    # Hard caps for basic (RM1-style) gating.
    max_single_order_notional: float = 50_000.0

    # If enabled, we also cap per-order notional using RM3 target weights.
    enforce_rm3_weight_limits: bool = False
    rm3_max_order_fraction_of_target: float = 1.25


@dataclass
class RiskManager:
    """Risk manager façade.

    This class is designed to be used by both:
    - ats.backtester2.engine.BacktestEngine (via evaluate_orders)
    - newer multi-stage pipelines (via apply + run_allocation_batch)

    RM3 is supported via run_allocation_batch/run_capital_batch, which updates
    `latest_symbol_weights` for downstream sizing/execution modules.
    """

    config: RiskConfig = field(default_factory=RiskConfig)
    capital_allocator: CapitalAllocator = field(default_factory=_make_default_allocator)

    bars_evaluated: int = 0
    orders_evaluated: int = 0
    orders_blocked: int = 0

    latest_symbol_weights: Dict[str, float] = field(default_factory=dict)
    last_capital_packets: List[CapitalAllocPacket] = field(default_factory=list)
    last_base_capital: float | None = None

    # ------------------------------------------------------------------
    # Bar helpers (avoid importing backtester2 types to prevent circulars)
    # ------------------------------------------------------------------
    def _bar_timestamp(self, bar: Any) -> str:
        if hasattr(bar, "timestamp"):
            return str(getattr(bar, "timestamp"))
        if isinstance(bar, Mapping) and "timestamp" in bar:
            return str(bar.get("timestamp"))
        return ""

    def _bar_symbol(self, bar: Any, orders: Sequence[Order]) -> str | None:
        if hasattr(bar, "symbol"):
            return str(getattr(bar, "symbol"))
        if isinstance(bar, Mapping) and "symbol" in bar:
            return str(bar.get("symbol"))
        if orders:
            return orders[0].symbol
        return None

    def _bar_price(self, bar: Any) -> float:
        for attr in ("close", "price", "last"):
            if hasattr(bar, attr):
                val = getattr(bar, attr)
                if val is not None:
                    return float(val)
        if isinstance(bar, Mapping):
            for key in ("close", "price", "last"):
                if key in bar and bar.get(key) is not None:
                    return float(bar[key])
        raise ValueError("Bar does not expose a usable price field (close/price/last).")

    # ------------------------------------------------------------------
    # Baseline RM gating for order batches (used by BacktestEngine)
    # ------------------------------------------------------------------
    def _check_order(self, order: Order, price: float) -> str | None:
        notional = abs(float(order.size) * float(price))

        if notional > float(self.config.max_single_order_notional):
            return (
                f"order_notional={notional:.2f} exceeds "
                f"max_single_order_notional={self.config.max_single_order_notional:.2f}"
            )

        if self.config.enforce_rm3_weight_limits and self.latest_symbol_weights:
            w = self.latest_symbol_weights.get(order.symbol)
            if w is not None:
                base = (
                    float(self.last_base_capital)
                    if self.last_base_capital is not None
                    else float(self.config.base_capital)
                )
                target_notional = abs(float(w)) * base

                if target_notional <= 0.0:
                    return "rm3_target_weight=0; blocking order under RM3 enforcement"

                cap = target_notional * float(
                    self.config.rm3_max_order_fraction_of_target
                )
                if notional > cap:
                    return f"order_notional={notional:.2f} exceeds rm3_cap={cap:.2f}"

        return None

    def evaluate_orders(self, bar: Any, orders: Sequence[Order]) -> RiskDecision:
        """Evaluate a list of candidate orders for a single bar."""
        self.bars_evaluated += 1
        self.orders_evaluated += len(orders)

        ts = self._bar_timestamp(bar)
        symbol = self._bar_symbol(bar, orders)
        price = self._bar_price(bar)

        accepted: List[Order] = []
        rejected: List[RejectedOrder] = []

        for o in orders:
            reason = self._check_order(o, price=price)
            if reason is None:
                accepted.append(o)
            else:
                rejected.append(RejectedOrder(order=o, reason=reason))
                self.orders_blocked += 1

        meta = {
            "price": price,
            "base_capital": self.last_base_capital or self.config.base_capital,
        }
        return RiskDecision(
            timestamp=ts,
            symbol=symbol,
            accepted_orders=accepted,
            rejected_orders=rejected,
            meta=meta,
        )

    # ------------------------------------------------------------------
    # RM3 wiring (capital packets -> weights; allocations -> packets -> weights)
    # ------------------------------------------------------------------
    def run_capital_batch(
        self,
        packets: Sequence[CapitalAllocPacket],
        base_capital: float | None = None,
    ) -> Dict[str, float]:
        """Consume RM3 packets and update latest_symbol_weights."""
        if not packets:
            self.latest_symbol_weights = {}
            self.last_capital_packets = []
            return {}

        base = (
            float(base_capital)
            if base_capital is not None
            else float(self.config.base_capital)
        )
        self.last_base_capital = base
        self.last_capital_packets = list(packets)

        # Support allocator.allocate(packets) and allocator.allocate(packets, base_capital=...)
        try:
            weights = self.capital_allocator.allocate(
                list(packets), base_capital=base  # type: ignore[call-arg]
            )
        except TypeError:
            weights = self.capital_allocator.allocate(list(packets))  # type: ignore[call-arg]

        self.latest_symbol_weights = dict(weights)
        return self.latest_symbol_weights

    def run_allocation_batch(
        self,
        allocations: Sequence[AggregatedAllocation],
        base_capital: float | None = None,
    ) -> Dict[str, float]:
        """Bridge: AggregatedAllocation[] -> CapitalAllocPacket[] -> RM3 weights."""
        base = (
            float(base_capital)
            if base_capital is not None
            else float(self.config.base_capital)
        )
        packets = _allocations_to_packets(allocations=allocations, base_capital=base)
        return self.run_capital_batch(packets, base_capital=base)

    def run_batch(
        self,
        batch: Mapping[str, Any],
        base_capital: float | None = None,
    ) -> Dict[str, float]:
        """Convenience: consume Aggregator.prepare_batch(...) output."""
        allocations = batch.get("allocations", [])
        if isinstance(allocations, list):
            return self.run_allocation_batch(allocations, base_capital=base_capital)
        return {}

    # ------------------------------------------------------------------
    # Compatibility shim for older pipelines calling RiskManager.apply(...)
    # ------------------------------------------------------------------
    def apply(self, *args: Any, **kwargs: Any) -> Any:
        """Compatibility shim for older pipelines.

        This method exists because multiple WIP backtester/orchestrator paths in
        the repo call RiskManager.apply(...). We keep it intentionally permissive.

        If the input resembles AggregatedAllocation[], we also update RM3 weights
        via run_allocation_batch().
        """
        if "combined_signals" in kwargs:
            signals = kwargs.get("combined_signals")
        elif args:
            signals = args[0]
        else:
            signals = None

        base_capital = kwargs.get("base_capital")
        if base_capital is None:
            base_capital = kwargs.get("equity") or kwargs.get("portfolio_value")
        if base_capital is None:
            base_capital = self.config.base_capital

        if self._looks_like_allocations(signals):
            self.run_allocation_batch(
                signals, base_capital=float(base_capital)  # type: ignore[arg-type]
            )

        return signals

    @staticmethod
    def _looks_like_allocations(obj: Any) -> bool:
        if not isinstance(obj, Sequence) or isinstance(obj, (str, bytes)):
            return False
        if not obj:
            return False
        first = obj[0]
        if not isinstance(first, Mapping):
            return False
        return "symbol" in first

    def summary(self) -> Dict[str, float]:
        return {
            "bars_evaluated": float(self.bars_evaluated),
            "orders_evaluated": float(self.orders_evaluated),
            "orders_blocked": float(self.orders_blocked),
        }
