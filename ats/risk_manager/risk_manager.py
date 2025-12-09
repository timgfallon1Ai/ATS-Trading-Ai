from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Sequence

from ats.trader.order_types import Order


@dataclass
class RiskConfig:
    """
    Baseline numeric risk configuration.

    These limits are deliberately simple and local to each order so the
    risk manager does not need deep knowledge of the portfolio yet.

    - max_size_per_order: maximum absolute unit size of any single order.
    - max_notional_per_order: maximum dollar notional of any single order,
      computed as abs(size) * reference_price.
    """

    max_size_per_order: float = 100.0
    max_notional_per_order: float = 10_000.0


@dataclass
class RiskDecision:
    """
    Result of evaluating a batch of candidate orders.

    - accepted_orders: orders that passed all checks and may be sent on to
      execution (e.g. Trader).
    - rejected_orders: orders that failed one or more checks.
    - reasons: mapping from the index of the original order in the input
      sequence to a short string describing why it was rejected.
    """

    accepted_orders: List[Order] = field(default_factory=list)
    rejected_orders: List[Order] = field(default_factory=list)
    reasons: Dict[int, str] = field(default_factory=dict)


class RiskManager:
    """
    Baseline risk manager.

    This implementation is intentionally "local": it only inspects
    the properties of each incoming order and a simple reference price
    from the current market snapshot.

    The `market` argument is treated as a generic object. In backtests,
    this will typically be a `Bar` with a `.close` attribute. In live
    trading, it could be any object that exposes a reasonable reference
    price via `.close` or `.price`.
    """

    def __init__(self, config: RiskConfig | None = None) -> None:
        self.config = config or RiskConfig()

    def evaluate_orders(self, market: Any, orders: Sequence[Order]) -> RiskDecision:
        """
        Apply baseline risk checks to a batch of candidate orders.

        Returns a RiskDecision with accepted and rejected orders separated.
        """
        decision = RiskDecision()

        # Resolve a reference price from the market snapshot.
        ref_price = self._resolve_price(market)

        for idx, order in enumerate(orders):
            size = float(getattr(order, "size", 0.0))
            side = getattr(order, "side", "unknown")
            symbol = getattr(order, "symbol", "UNKNOWN")

            # Per-order reference price: allow an explicit price on the order
            # to override the market snapshot if present.
            price = getattr(order, "price", None)
            if price is None:
                price = ref_price

            notional = abs(size) * price

            # Basic sanity checks.
            if size <= 0.0:
                decision.rejected_orders.append(order)
                decision.reasons[idx] = "non-positive order size"
                continue

            if abs(size) > self.config.max_size_per_order:
                decision.rejected_orders.append(order)
                decision.reasons[idx] = (
                    f"order size {size} exceeds max_size_per_order "
                    f"{self.config.max_size_per_order}"
                )
                continue

            if notional > self.config.max_notional_per_order:
                decision.rejected_orders.append(order)
                decision.reasons[idx] = (
                    f"order notional {notional:.2f} exceeds "
                    f"max_notional_per_order {self.config.max_notional_per_order:.2f}"
                )
                continue

            # If we get here, the order is accepted.
            decision.accepted_orders.append(order)

        return decision

    @staticmethod
    def _resolve_price(market: Any) -> float:
        """
        Try to extract a reasonable reference price from a market snapshot.
        """
        # Prefer `.close`, then `.price`, else fall back to 1.0 to avoid
        # divide-by-zero or degenerate notional calculations.
        for attr in ("close", "price"):
            if hasattr(market, attr):
                value = getattr(market, attr)
                try:
                    return float(value)
                except (TypeError, ValueError):
                    continue
        return 1.0
