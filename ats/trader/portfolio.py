from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Mapping

from .fill_types import Fill
from .position_book import PositionBook


def _sign(x: float) -> int:
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


@dataclass
class Portfolio:
    """
    Portfolio bookkeeping for the "thin trader" (T1).

    This module is intentionally **execution-agnostic**:
    - It does not decide what to trade (that's Analyst/Aggregator/RM).
    - It only applies fills and produces a valuation snapshot.

    Key features:
    - Supports long AND short positions (signed quantities).
    - Correct realized P&L when reducing/closing/reversing positions.
    - Optional fee model (bps + per-share).
    - Convenience metrics for risk/monitoring (equity, exposure, unrealized P&L).
    - "Two-pool" telemetry helpers:
        * `principal_floor` (protected principal baseline)
        * computed principal/profit equity buckets
        * `aggressive_enabled` flag based on realized P&L threshold

    Notes on the "two-pool" concept:
    This class does NOT enforce your RM7 principal shield rules (that's risk_manager's job).
    It does provide consistent accounting signals so RM7/monitoring can enforce invariants.
    """

    starting_cash: float = 100_000.0

    # --- Principal / profits telemetry (does not enforce risk) ---
    principal_floor: float | None = None
    aggressive_rpl_threshold: float = 1_000.0  # "aggressive mode above +$1k RPL"

    # --- Fee model ---
    fee_bps: float = 0.0  # charged on notional, e.g., 1.0 = 1bp
    fee_per_share: float = 0.0  # charged on abs(shares)

    # If True, allow cash to go negative (margin-style backtests).
    allow_negative_cash: bool = True

    # --- Runtime state ---
    cash: float = field(init=False)
    realized_pnl: float = field(init=False)
    fees_paid: float = field(init=False)
    positions: PositionBook = field(init=False)

    def __post_init__(self) -> None:
        self.cash = float(self.starting_cash)
        self.realized_pnl = 0.0
        self.fees_paid = 0.0
        self.positions = PositionBook()

        if self.principal_floor is None:
            # Default: treat the starting cash as the protected principal baseline.
            self.principal_floor = float(self.starting_cash)

    # ------------------------------------------------------------------ #
    # Fees
    # ------------------------------------------------------------------ #

    def _fee_for_fill(self, fill: Fill) -> float:
        """
        Compute fees for a fill.

        - fee_bps applies to abs(notional) (buy/sell same fee magnitude).
        - fee_per_share applies to abs(size).
        """
        notional_abs = abs(fill.size * fill.price)
        fee = 0.0
        if self.fee_bps:
            fee += notional_abs * (self.fee_bps / 10_000.0)
        if self.fee_per_share:
            fee += abs(fill.size) * self.fee_per_share
        return float(fee)

    # ------------------------------------------------------------------ #
    # Fill application
    # ------------------------------------------------------------------ #

    def apply_fill(self, fill: Fill) -> None:
        """
        Apply a single execution fill to the portfolio.

        Conventions:
        - Position quantities are signed:
            long  => quantity > 0
            short => quantity < 0
        - Fill.size must be positive.
        """
        if fill.size <= 0:
            raise ValueError("Fill.size must be positive")

        pos = self.positions.get(fill.symbol)
        old_qty = float(pos.quantity)

        # Cash moves on every fill (simple cash model).
        if fill.side == "buy":
            self.cash -= fill.size * fill.price
            qty_delta = float(fill.size)
        elif fill.side == "sell":
            self.cash += fill.size * fill.price
            qty_delta = -float(fill.size)
        else:
            raise ValueError(f"Invalid Fill.side: {fill.side!r}")

        # Apply fees immediately (fees reduce equity and realized P&L).
        fee = self._fee_for_fill(fill)
        if fee:
            self.cash -= fee
            self.fees_paid += fee
            self.realized_pnl -= fee

        # No existing position -> open new.
        if old_qty == 0.0:
            pos.quantity = qty_delta
            pos.avg_price = float(fill.price) if qty_delta != 0.0 else 0.0
            self._enforce_cash_constraint()
            return

        new_qty = old_qty + qty_delta

        # Case 1: Increasing same-direction position (no realized P&L).
        if _sign(old_qty) == _sign(new_qty) and abs(new_qty) > abs(old_qty):
            total_abs = abs(old_qty) + abs(qty_delta)
            # Weighted average entry price using absolute sizes.
            pos.avg_price = (
                abs(old_qty) * pos.avg_price + abs(qty_delta) * fill.price
            ) / max(total_abs, 1e-12)
            pos.quantity = new_qty
            self._enforce_cash_constraint()
            return

        # Case 2: Reducing position (partial close) or closing/reversing.
        # Closing quantity is the amount that offsets the existing position.
        closing_qty = min(abs(old_qty), abs(qty_delta))

        # Realized P&L:
        # long close via sell:  (exit - entry) * qty
        # short close via buy:  (entry - exit) * qty
        realized = (
            closing_qty * (fill.price - pos.avg_price) * (1.0 if old_qty > 0 else -1.0)
        )
        self.realized_pnl += float(realized)

        if new_qty == 0.0:
            # Fully flat.
            pos.quantity = 0.0
            pos.avg_price = 0.0
            self._enforce_cash_constraint()
            return

        if _sign(old_qty) == _sign(new_qty):
            # Partial close but still same direction -> avg_price unchanged.
            pos.quantity = new_qty
            self._enforce_cash_constraint()
            return

        # Reversal: close old position fully, open new remainder in opposite direction at fill.price.
        pos.quantity = new_qty
        pos.avg_price = float(fill.price)
        self._enforce_cash_constraint()

    def apply_fills(self, fills: list[Fill]) -> None:
        """Apply a batch of fills in-order."""
        for fill in fills:
            self.apply_fill(fill)

    def _enforce_cash_constraint(self) -> None:
        if self.allow_negative_cash:
            return
        if self.cash < -1e-6:
            raise ValueError(
                f"Cash went negative ({self.cash:.2f}) with allow_negative_cash=False"
            )

    # ------------------------------------------------------------------ #
    # Valuation / risk telemetry
    # ------------------------------------------------------------------ #

    def positions_value(self, prices: Mapping[str, float]) -> float:
        """Marked-to-market signed value of positions: sum(quantity * price)."""
        value = 0.0
        for symbol, pos in self.positions.all().items():
            if pos.quantity == 0:
                continue
            px = float(prices.get(symbol, pos.avg_price))
            value += float(pos.quantity) * px
        return float(value)

    def unrealized_pnl(self, prices: Mapping[str, float]) -> float:
        """
        Mark-to-market unrealized P&L of open positions.

        Works for long and short via the identity:
            unrealized = (mark - avg) * quantity
        (quantity is signed).
        """
        pnl = 0.0
        for symbol, pos in self.positions.all().items():
            if pos.quantity == 0:
                continue
            px = float(prices.get(symbol, pos.avg_price))
            pnl += (px - float(pos.avg_price)) * float(pos.quantity)
        return float(pnl)

    def equity(self, prices: Mapping[str, float]) -> float:
        """Total equity = cash + marked-to-market position value."""
        return float(self.cash + self.positions_value(prices))

    def gross_exposure(self, prices: Mapping[str, float]) -> float:
        """Gross exposure = sum(abs(quantity * price))."""
        gross = 0.0
        for symbol, pos in self.positions.all().items():
            if pos.quantity == 0:
                continue
            px = float(prices.get(symbol, pos.avg_price))
            gross += abs(float(pos.quantity) * px)
        return float(gross)

    def net_exposure(self, prices: Mapping[str, float]) -> float:
        """Net exposure = sum(quantity * price)."""
        return float(self.positions_value(prices))

    # ------------------------------------------------------------------ #
    # Principal / profit helpers (telemetry only)
    # ------------------------------------------------------------------ #

    @property
    def aggressive_enabled(self) -> bool:
        """True if realized P&L crosses the configured threshold."""
        return bool(self.realized_pnl >= float(self.aggressive_rpl_threshold))

    def equity_pools(self, prices: Mapping[str, float]) -> Dict[str, float]:
        """
        Return (principal_equity, profit_equity) buckets based on current equity.

        principal_equity is capped at `principal_floor` (your protected baseline).
        profit_equity is any equity above that floor.

        This is a *telemetry* decomposition — it does not enforce trading rules.
        """
        floor = float(self.principal_floor or 0.0)
        eq = self.equity(prices)
        principal_equity = min(eq, floor)
        profit_equity = max(0.0, eq - floor)
        return {
            "principal_floor": floor,
            "principal_equity": float(principal_equity),
            "profit_equity": float(profit_equity),
        }

    # ------------------------------------------------------------------ #
    # Serialization
    # ------------------------------------------------------------------ #

    def snapshot(self, prices: Mapping[str, float]) -> Dict[str, object]:
        """
        Return a JSON-serializable snapshot of portfolio state.

        This is designed to be safe for logs/dashboards.
        """
        pos_out: Dict[str, Dict[str, float]] = {}
        for symbol, pos in self.positions.all().items():
            if pos.quantity == 0:
                continue
            mark = float(prices.get(symbol, pos.avg_price))
            pos_out[symbol] = {
                "quantity": float(pos.quantity),
                "avg_price": float(pos.avg_price),
                "mark_price": mark,
                "market_value": float(pos.quantity) * mark,
                "unrealized_pnl": (mark - float(pos.avg_price)) * float(pos.quantity),
            }

        eq = self.equity(prices)
        pools = self.equity_pools(prices)

        return {
            "cash": float(self.cash),
            "starting_cash": float(self.starting_cash),
            "principal_floor": float(self.principal_floor or 0.0),
            "realized_pnl": float(self.realized_pnl),
            "unrealized_pnl": float(self.unrealized_pnl(prices)),
            "fees_paid": float(self.fees_paid),
            "equity": float(eq),
            "gross_exposure": float(self.gross_exposure(prices)),
            "net_exposure": float(self.net_exposure(prices)),
            "aggressive_enabled": bool(self.aggressive_enabled),
            "pools": pools,
            "positions": pos_out,
        }
