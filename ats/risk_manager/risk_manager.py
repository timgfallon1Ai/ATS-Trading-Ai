from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from ats.trader.order_types import Order
from ats.types import AggregatedAllocation, CapitalAllocPacket

# ---------------------------------------------------------------------
# RM3 allocator imports (best-effort compatible)
# ---------------------------------------------------------------------
try:
    from .rm3_capital.capital_allocator import CapitalAllocator, CapitalAllocatorConfig
except Exception:  # pragma: no cover
    from .rm3_capital.capital_allocator import CapitalAllocator  # type: ignore

    CapitalAllocatorConfig = None  # type: ignore[assignment]


def _make_default_allocator() -> CapitalAllocator:
    if CapitalAllocatorConfig is None:
        return CapitalAllocator()  # type: ignore[call-arg]
    try:
        return CapitalAllocator(CapitalAllocatorConfig())  # type: ignore[arg-type]
    except TypeError:
        return CapitalAllocator()  # type: ignore[call-arg]


# ---------------------------------------------------------------------
# RM bridge import (support multiple bridge shapes)
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
# Public contracts
# ---------------------------------------------------------------------
@dataclass(frozen=True)
class RejectedOrder:
    order: Order
    reason: str


@dataclass
class RiskDecision:
    timestamp: str
    symbol: Optional[str] = None
    accepted_orders: List[Order] = field(default_factory=list)
    rejected_orders: List[RejectedOrder] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskConfig:
    # Baseline notional cap
    max_single_order_notional: float = 50_000.0

    # Default notional "book size" used when interpreting weights (RM3)
    base_capital: float = 1_000_000.0

    # Optional RM3 order cap enforcement
    enforce_rm3_weight_limits: bool = False
    rm3_max_order_fraction_of_target: float = 1.25

    # Portfolio invariant enforcement (Phase9.2)
    enforce_portfolio_halt: bool = True
    enforce_exposure_caps: bool = True

    # Aggressive gate threshold (fallback if portfolio snapshot doesn’t include aggressive_enabled)
    aggressive_profit_threshold: float = 1_000.0

    # Exposure limits (fractions of capital-for-limits)
    # - principal mode: limits applied on principal_floor only
    # - aggressive mode: limits applied on principal_floor + profit_equity
    max_gross_exposure_principal_frac: float = 0.25
    max_net_exposure_principal_frac: float = 0.25

    max_gross_exposure_aggressive_frac: float = 1.00
    max_net_exposure_aggressive_frac: float = 1.00

    # Per-symbol cap (abs exposure) as fraction of capital-for-limits
    max_symbol_exposure_frac: float = 0.20

    # Numeric tolerance to avoid flaky float comparisons
    exposure_epsilon: float = 1e-9
    floor_breach_tolerance: float = 1e-6


@dataclass
class _PortfolioState:
    equity: Optional[float]
    principal_floor: Optional[float]
    profit_equity: float
    aggressive_enabled: bool
    halted: bool
    halted_reason: Optional[str]
    gross_exposure: float
    net_exposure: float
    qty_by_symbol: Dict[str, float]

    @staticmethod
    def _to_float(x: Any) -> Optional[float]:
        try:
            if x is None:
                return None
            return float(x)
        except Exception:
            return None

    @classmethod
    def from_snapshot(
        cls,
        snapshot: Mapping[str, Any],
        *,
        aggressive_profit_threshold: float,
        floor_breach_tolerance: float,
    ) -> "_PortfolioState":
        pools = (
            snapshot.get("pools") if isinstance(snapshot.get("pools"), Mapping) else {}
        )

        equity = cls._to_float(snapshot.get("equity"))
        principal_floor = cls._to_float(snapshot.get("principal_floor"))
        if principal_floor is None:
            principal_floor = cls._to_float(pools.get("principal_floor"))

        profit_equity = cls._to_float(pools.get("profit_equity"))
        if profit_equity is None:
            if equity is not None and principal_floor is not None:
                profit_equity = max(0.0, equity - principal_floor)
            else:
                profit_equity = 0.0

        # Aggressive: trust snapshot if present else compute.
        aggressive_enabled = snapshot.get("aggressive_enabled")
        if isinstance(aggressive_enabled, bool):
            aggressive = aggressive_enabled
        else:
            aggressive = profit_equity >= float(aggressive_profit_threshold)

        # Halt: trust snapshot if present else compute floor breach
        halted_val = snapshot.get("halted")
        halted_reason = snapshot.get("halted_reason")
        if isinstance(halted_val, bool):
            halted = halted_val
            halted_reason_out = (
                str(halted_reason) if halted_reason is not None else None
            )
        else:
            halted_reason_out = None
            halted = False
            if equity is not None and principal_floor is not None:
                if equity < principal_floor - float(floor_breach_tolerance):
                    halted = True
                    halted_reason_out = f"principal_floor_breach equity={equity:.6f} < floor={principal_floor:.6f}"

        gross_exposure = cls._to_float(snapshot.get("gross_exposure"))
        if gross_exposure is None:
            gross_exposure = 0.0

        net_exposure = cls._to_float(snapshot.get("net_exposure"))
        if net_exposure is None:
            net_exposure = 0.0

        qty_by_symbol: Dict[str, float] = {}
        positions = snapshot.get("positions")
        if isinstance(positions, Mapping):
            for sym, pos in positions.items():
                if not isinstance(pos, Mapping):
                    continue
                q = cls._to_float(pos.get("quantity"))
                if q is None:
                    continue
                qty_by_symbol[str(sym)] = float(q)

        return cls(
            equity=equity,
            principal_floor=principal_floor,
            profit_equity=float(profit_equity),
            aggressive_enabled=bool(aggressive),
            halted=bool(halted),
            halted_reason=halted_reason_out,
            gross_exposure=float(gross_exposure),
            net_exposure=float(net_exposure),
            qty_by_symbol=qty_by_symbol,
        )


@dataclass
class _ExposureCaps:
    gross_cap: float
    net_abs_cap: float
    symbol_abs_cap: float
    capital_for_limits: float


@dataclass
class _ExposureState:
    gross: float
    net: float
    qty_by_symbol: Dict[str, float]


def _bar_timestamp(bar: Any) -> str:
    if hasattr(bar, "timestamp"):
        return str(getattr(bar, "timestamp"))
    if isinstance(bar, Mapping) and "timestamp" in bar:
        return str(bar.get("timestamp"))
    return ""


def _bar_symbol(bar: Any, orders: Sequence[Order]) -> Optional[str]:
    if hasattr(bar, "symbol"):
        return str(getattr(bar, "symbol"))
    if isinstance(bar, Mapping) and "symbol" in bar:
        return str(bar.get("symbol"))
    if orders:
        return orders[0].symbol
    return None


def _bar_price(bar: Any) -> float:
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


@dataclass
class RiskManager:
    config: RiskConfig = field(default_factory=RiskConfig)
    capital_allocator: CapitalAllocator = field(default_factory=_make_default_allocator)

    bars_evaluated: int = 0
    orders_evaluated: int = 0
    orders_blocked: int = 0

    latest_symbol_weights: Dict[str, float] = field(default_factory=dict)
    last_capital_packets: List[CapitalAllocPacket] = field(default_factory=list)
    last_base_capital: Optional[float] = None

    # ------------------------------------------------------------------
    # RM3 wiring
    # ------------------------------------------------------------------
    def run_capital_batch(
        self,
        packets: Sequence[CapitalAllocPacket],
        base_capital: Optional[float] = None,
    ) -> Dict[str, float]:
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

        try:
            weights = self.capital_allocator.allocate(list(packets), base_capital=base)  # type: ignore[call-arg]
        except TypeError:
            weights = self.capital_allocator.allocate(list(packets))  # type: ignore[call-arg]

        self.latest_symbol_weights = dict(weights)
        return self.latest_symbol_weights

    def run_allocation_batch(
        self,
        allocations: Sequence[AggregatedAllocation],
        base_capital: Optional[float] = None,
    ) -> Dict[str, float]:
        base = (
            float(base_capital)
            if base_capital is not None
            else float(self.config.base_capital)
        )
        packets = _allocations_to_packets(allocations=allocations, base_capital=base)
        return self.run_capital_batch(packets, base_capital=base)

    def run_batch(
        self, batch: Mapping[str, Any], base_capital: Optional[float] = None
    ) -> Dict[str, float]:
        allocations = batch.get("allocations", [])
        if isinstance(allocations, list):
            return self.run_allocation_batch(allocations, base_capital=base_capital)
        return {}

    # ------------------------------------------------------------------
    # Order evaluation (Phase9.2 invariants)
    # ------------------------------------------------------------------
    def _caps_from_portfolio(self, ps: _PortfolioState) -> _ExposureCaps:
        principal = (
            ps.principal_floor
            if ps.principal_floor is not None
            else float(self.config.base_capital)
        )
        principal = float(principal)

        # Capital-for-limits: principal only until aggressive is enabled.
        capital_for_limits = principal + (
            ps.profit_equity if ps.aggressive_enabled else 0.0
        )

        if ps.aggressive_enabled:
            gross_cap = capital_for_limits * float(
                self.config.max_gross_exposure_aggressive_frac
            )
            net_abs_cap = capital_for_limits * float(
                self.config.max_net_exposure_aggressive_frac
            )
        else:
            gross_cap = principal * float(self.config.max_gross_exposure_principal_frac)
            net_abs_cap = principal * float(self.config.max_net_exposure_principal_frac)

        symbol_abs_cap = capital_for_limits * float(
            self.config.max_symbol_exposure_frac
        )
        return _ExposureCaps(
            gross_cap=float(gross_cap),
            net_abs_cap=float(net_abs_cap),
            symbol_abs_cap=float(symbol_abs_cap),
            capital_for_limits=float(capital_for_limits),
        )

    @staticmethod
    def _delta_qty(order: Order) -> float:
        if order.side == "buy":
            return float(order.size)
        if order.side == "sell":
            return -float(order.size)
        raise ValueError(f"Unexpected order.side={order.side!r}")

    def _simulate_exposures_after(
        self,
        state: _ExposureState,
        *,
        symbol: str,
        price: float,
        delta_qty: float,
    ) -> Tuple[float, float, float, float]:
        """Return (gross_after, net_after, new_qty, new_mv)."""
        old_qty = float(state.qty_by_symbol.get(symbol, 0.0))
        new_qty = old_qty + float(delta_qty)

        old_mv = old_qty * float(price)
        new_mv = new_qty * float(price)

        gross_after = float(state.gross) - abs(old_mv) + abs(new_mv)
        net_after = float(state.net) - old_mv + new_mv
        return gross_after, net_after, new_qty, new_mv

    def _check_order(
        self,
        order: Order,
        *,
        price: float,
        portfolio_state: Optional[_PortfolioState],
        exposure_state: Optional[_ExposureState],
    ) -> Optional[str]:
        notional = abs(float(order.size) * float(price))

        if notional > float(self.config.max_single_order_notional):
            return (
                f"order_notional={notional:.2f} exceeds "
                f"max_single_order_notional={self.config.max_single_order_notional:.2f}"
            )

        # Portfolio halt (hard stop)
        if (
            portfolio_state is not None
            and self.config.enforce_portfolio_halt
            and portfolio_state.halted
        ):
            reason = portfolio_state.halted_reason or "portfolio_halted"
            return f"portfolio_halted: {reason}"

        # Exposure caps (gross/net/symbol)
        if (
            portfolio_state is not None
            and exposure_state is not None
            and self.config.enforce_exposure_caps
        ):
            caps = self._caps_from_portfolio(portfolio_state)

            delta_qty = self._delta_qty(order)
            gross_after, net_after, new_qty, new_mv = self._simulate_exposures_after(
                exposure_state,
                symbol=order.symbol,
                price=price,
                delta_qty=delta_qty,
            )

            eps = float(self.config.exposure_epsilon)

            if gross_after > caps.gross_cap + eps:
                return (
                    f"gross_exposure_cap breached: gross_after={gross_after:.2f} > "
                    f"cap={caps.gross_cap:.2f} (capital_for_limits={caps.capital_for_limits:.2f})"
                )

            if abs(net_after) > caps.net_abs_cap + eps:
                return (
                    f"net_exposure_cap breached: |net_after|={abs(net_after):.2f} > "
                    f"cap={caps.net_abs_cap:.2f} (capital_for_limits={caps.capital_for_limits:.2f})"
                )

            if abs(new_mv) > caps.symbol_abs_cap + eps:
                return (
                    f"symbol_exposure_cap breached for {order.symbol}: |mv_after|={abs(new_mv):.2f} > "
                    f"cap={caps.symbol_abs_cap:.2f} (new_qty={new_qty:.4f})"
                )

        # Optional RM3-based cap (if weights have been computed)
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

    def evaluate_orders(
        self,
        bar: Any,
        orders: Sequence[Order],
        *,
        portfolio: Optional[Mapping[str, Any]] = None,
        portfolio_snapshot: Optional[Mapping[str, Any]] = None,
    ) -> RiskDecision:
        """Evaluate a batch of candidate orders for a bar.

        `portfolio` / `portfolio_snapshot` are optional and enable Phase9.2 invariant enforcement.
        If omitted, only max_notional and optional RM3 limits are enforced.
        """
        self.bars_evaluated += 1
        self.orders_evaluated += len(orders)

        ts = _bar_timestamp(bar)
        symbol = _bar_symbol(bar, orders)
        price = _bar_price(bar)

        snapshot = portfolio_snapshot if portfolio_snapshot is not None else portfolio

        ps: Optional[_PortfolioState] = None
        es: Optional[_ExposureState] = None

        if snapshot is not None:
            ps = _PortfolioState.from_snapshot(
                snapshot,
                aggressive_profit_threshold=float(
                    self.config.aggressive_profit_threshold
                ),
                floor_breach_tolerance=float(self.config.floor_breach_tolerance),
            )
            es = _ExposureState(
                gross=float(ps.gross_exposure),
                net=float(ps.net_exposure),
                qty_by_symbol=dict(ps.qty_by_symbol),
            )

        accepted: List[Order] = []
        rejected: List[RejectedOrder] = []

        gross_before = es.gross if es is not None else None
        net_before = es.net if es is not None else None

        for o in orders:
            reason = self._check_order(
                o,
                price=price,
                portfolio_state=ps,
                exposure_state=es,
            )
            if reason is None:
                accepted.append(o)
                if es is not None:
                    dq = self._delta_qty(o)
                    gross_after, net_after, new_qty, _ = self._simulate_exposures_after(
                        es, symbol=o.symbol, price=price, delta_qty=dq
                    )
                    es.gross = float(gross_after)
                    es.net = float(net_after)
                    es.qty_by_symbol[o.symbol] = float(new_qty)
            else:
                rejected.append(RejectedOrder(order=o, reason=reason))
                self.orders_blocked += 1

        meta: Dict[str, Any] = {
            "price": price,
        }
        if ps is not None:
            meta.update(
                {
                    "portfolio_equity": ps.equity,
                    "principal_floor": ps.principal_floor,
                    "profit_equity": ps.profit_equity,
                    "aggressive_enabled": ps.aggressive_enabled,
                    "halted": ps.halted,
                    "halted_reason": ps.halted_reason,
                    "gross_before": gross_before,
                    "net_before": net_before,
                    "gross_after": es.gross if es is not None else None,
                    "net_after": es.net if es is not None else None,
                }
            )

        return RiskDecision(
            timestamp=ts,
            symbol=symbol,
            accepted_orders=accepted,
            rejected_orders=rejected,
            meta=meta,
        )

    # ------------------------------------------------------------------
    # Compatibility shim for older pipelines calling RiskManager.apply(...)
    # ------------------------------------------------------------------
    def apply(self, *args: Any, **kwargs: Any) -> Any:
        # Keep permissive; if it looks like allocations, update RM3 weights.
        signals = (
            kwargs.get("combined_signals")
            if "combined_signals" in kwargs
            else (args[0] if args else None)
        )
        base_capital = (
            kwargs.get("base_capital")
            or kwargs.get("equity")
            or kwargs.get("portfolio_value")
            or self.config.base_capital
        )

        if self._looks_like_allocations(signals):
            self.run_allocation_batch(signals, base_capital=float(base_capital))  # type: ignore[arg-type]

        return signals

    @staticmethod
    def _looks_like_allocations(obj: Any) -> bool:
        if not isinstance(obj, Sequence) or isinstance(obj, (str, bytes)):
            return False
        if not obj:
            return False
        first = obj[0]
        return isinstance(first, Mapping) and ("symbol" in first)
